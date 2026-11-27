#pragma once
// Optional UI-only NVMe observation. No actuator or storage mutation.
#include <windows.h>
#include <winioctl.h>
#include <array>
#include <atomic>
#include <memory>
#include <thread>
#include <cwchar>
#include <cstring>
#include "nvme_thermal.h"

namespace nvme_monitor {
using smart_policy::ThermalState;
struct Snapshot {
    unsigned count=0, unavailable=0, disk=0;
    unsigned temperature=0;
    ThermalState state=ThermalState::Unknown;
    uint64_t sampled=0;
};
class DiskHandle {
public:
    explicit DiskHandle(HANDLE value): h(value) {}
    ~DiskHandle(){if(h!=INVALID_HANDLE_VALUE)CloseHandle(h);}
    DiskHandle(const DiskHandle&)=delete;
    DiskHandle& operator=(const DiskHandle&)=delete;
    HANDLE h;
};
inline bool query(HANDLE h, uint32_t type, uint32_t value, void* dst, size_t n) {
    // STORAGE_PROPERTY_QUERY followed by STORAGE_PROTOCOL_SPECIFIC_DATA.
    // Same standard read path previously verified on PM991.
    for (uint32_t property : {49u,50u}) {
        std::array<uint32_t,12+1024> b{};
        b[0]=property;b[2]=3;b[3]=type;b[4]=value;b[6]=40;b[7]=static_cast<uint32_t>(n);
        DWORD returned=0;
        const DWORD bytes=static_cast<DWORD>(48+n);
        if (!DeviceIoControl(h,IOCTL_STORAGE_QUERY_PROPERTY,b.data(),bytes,
            b.data(),bytes,&returned,nullptr))continue;
        size_t offset=0;
        if(returned<=bytes && smart_policy::nvme_payload(b.data(),returned,type,n,offset)){
            std::memcpy(dst,reinterpret_cast<const unsigned char*>(b.data())+offset,n);
            return true;
        }
    }
    return false;
}
inline Snapshot scan() {
    Snapshot out{};
    const uint64_t start=GetTickCount64();
    std::array<wchar_t,32768> names{};
    if(!QueryDosDeviceW(nullptr,names.data(),static_cast<DWORD>(names.size())))return out;
    for(const wchar_t* p=names.data();*p;p+=wcslen(p)+1){
        const wchar_t prefix[]=L"PhysicalDrive";
        if(wcsncmp(p,prefix,13)!=0 || !p[13])continue;
        unsigned disk=0;bool numeric=true;
        for(const wchar_t* c=p+13;*c;++c){
            if(*c<L'0'||*c>L'9'||disk>9999){numeric=false;break;}
            disk=disk*10+static_cast<unsigned>(*c-L'0');
        }
        if(!numeric)continue;
        wchar_t path[64]{};
        if(swprintf_s(path,64,L"\\\\.\\PhysicalDrive%u",disk)<0)continue;
        DiskHandle handle(CreateFileW(path,0,FILE_SHARE_READ|FILE_SHARE_WRITE,
            nullptr,OPEN_EXISTING,0,nullptr));
        if(handle.h==INVALID_HANDLE_VALUE){++out.unavailable;continue;}
        BOOL awake=TRUE;
        if(GetDevicePowerState(handle.h,&awake)&&!awake){++out.unavailable;continue;}
        STORAGE_PROPERTY_QUERY property{};
        property.PropertyId=StorageDeviceProperty;
        property.QueryType=PropertyStandardQuery;
        alignas(STORAGE_DEVICE_DESCRIPTOR) unsigned char descriptor[1024]{};
        DWORD returned=0;
        if(!DeviceIoControl(handle.h,IOCTL_STORAGE_QUERY_PROPERTY,&property,sizeof(property),
            descriptor,sizeof(descriptor),&returned,nullptr) ||
            returned<offsetof(STORAGE_DEVICE_DESCRIPTOR,RawDeviceProperties)){
            ++out.unavailable;continue;
        }
        const auto* d=reinterpret_cast<const STORAGE_DEVICE_DESCRIPTOR*>(descriptor);
        if(d->BusType!=BusTypeNvme)continue;
        ++out.count;
        std::array<uint8_t,4096> identify{};
        std::array<uint8_t,512> health{};
        const bool id=query(handle.h,1,1,identify.data(),identify.size());
        smart_policy::NvmeThermal n{};
        if(!query(handle.h,2,2,health.data(),health.size()) ||
            !smart_policy::decode_nvme_thermal(health.data(),health.size(),
                id?identify.data():nullptr,id?identify.size():0,GetTickCount64(),n)){
            ++out.unavailable;continue;
        }
        const auto s=smart_policy::nvme_thermal_state(n,GetTickCount64(),45000,5);
        if(s==ThermalState::Unknown)++out.unavailable;
        if(!out.temperature || s>out.state || (s==out.state && n.temperature_k>out.temperature)){
            out.disk=disk;out.temperature=n.temperature_k;out.state=s;
        }
    }
    if(out.state==ThermalState::Normal && out.unavailable)out.state=ThermalState::Unknown;
    out.sampled=GetTickCount64();
    // Reject long scans: the oldest disk may already be stale.
    if(out.sampled-start>5000)return Snapshot{};
    return out;
}
// One in-flight scan. A detached worker owns only its result, never FANCONTROL.
// If a disk driver stalls, the UI and fan engine continue; no new worker is spawned.
class Monitor {
    struct Job {Snapshot value;std::atomic<bool> done{false};};
public:
    bool poll(uint64_t now) {
        if(job_ && job_->done.load(std::memory_order_acquire)){
            if(!discard_)current_=job_->value;
            job_.reset();discard_=false;
            next_=now+15000;
            return true;
        }
        if(!job_ && now>=next_){
            next_=now+15000;
            try {
                auto job=std::make_shared<Job>();
                std::thread([job]{
                    try {job->value=scan();}catch(...){job->value=Snapshot{};}
                    job->done.store(true,std::memory_order_release);
                }).detach();
                job_=job;
            }catch(...){current_=Snapshot{};}
        }
        return false;
    }
    void invalidate(){current_=Snapshot{};discard_=true;next_=0;if(!job_)discard_=false;}
    Snapshot current(uint64_t now) const {
        if(!current_.sampled || now<current_.sampled || now-current_.sampled>45000)return Snapshot{};
        return current_;
    }
private:
    std::shared_ptr<Job> job_;
    Snapshot current_;
    uint64_t next_=0;
    bool discard_=false;
};
}
