#pragma once
// Narrow read-only adapter for the official signed IntelMSR PawnIO module.
// One processor group, one package, unrestricted process affinity only.
#include <windows.h>
#include <winioctl.h>
#include <intrin.h>
#include <cstdio>
#include <cstring>
#include <vector>
#include "cpu_msr.h"
namespace cpu_msr {
class Reader {
public:
    Reader() = default;
    Reader(const Reader&) = delete;
    Reader& operator=(const Reader&) = delete;
    ~Reader() { close(); }
    void close() {
        if (handle_ != INVALID_HANDLE_VALUE) CloseHandle(handle_);
        handle_ = INVALID_HANDLE_VALUE;
        energy_.reset();
    }
    bool open(const wchar_t* file) {
        close();
        // Keep the application's legacy Windows target. MSR telemetry is
        // optional and fails closed when processor-group APIs are absent.
        using GroupCount = WORD (WINAPI*)();
        const auto kernel = GetModuleHandleW(L"kernel32.dll");
        const auto group_count = kernel ? reinterpret_cast<GroupCount>(
            GetProcAddress(kernel,"GetActiveProcessorGroupCount")) : nullptr;
        if(!group_count || group_count()!=1)return false;
        int cp[4]{};
        __cpuid(cp,0);
        if (cp[0]<6 || cp[1]!=0x756e6547 || cp[3]!=0x49656e69 || cp[2]!=0x6c65746e) return false;
        __cpuid(cp,6);
        if (!(cp[0]&1) || !(cp[0]&(1<<6))) return false;
        DWORD bytes=0;
        GetLogicalProcessorInformation(nullptr,&bytes);
        if (!bytes || bytes>65536 || bytes%sizeof(SYSTEM_LOGICAL_PROCESSOR_INFORMATION)) return false;
        std::vector<SYSTEM_LOGICAL_PROCESSOR_INFORMATION> topology(bytes/sizeof(SYSTEM_LOGICAL_PROCESSOR_INFORMATION));
        if (!GetLogicalProcessorInformation(topology.data(),&bytes)) return false;
        unsigned packages=0; DWORD_PTR package_mask=0;
        for (size_t i=0;i<bytes/sizeof(topology[0]);++i)
            if(topology[i].Relationship==RelationProcessorPackage){++packages;package_mask=topology[i].ProcessorMask;}
        DWORD_PTR system=0, process=0;
        if (packages!=1 || !GetProcessAffinityMask(GetCurrentProcess(),&process,&system) ||
            !process || process!=system || process!=package_mask) return false;
        mask_=process;
        FILE* f=nullptr;
        if (_wfopen_s(&f,file,L"rb") || !f) return false;
        unsigned char blob[65536];
        const size_t n=fread(blob,1,sizeof(blob),f);
        const bool complete=feof(f)!=0 && !ferror(f);
        fclose(f);
        if(!complete || !n) return false;
        handle_=CreateFileW(L"\\\\.\\GLOBALROOT\\Device\\PawnIO",GENERIC_READ|GENERIC_WRITE,
            FILE_SHARE_READ|FILE_SHARE_WRITE,nullptr,OPEN_EXISTING,0,nullptr);
        if(handle_==INVALID_HANDLE_VALUE)return false;
        DWORD returned=0;
        if(!DeviceIoControl(handle_,CTL_CODE(41394u,0x821u,METHOD_BUFFERED,FILE_ANY_ACCESS),
            blob,static_cast<DWORD>(n),nullptr,0,&returned,nullptr) || returned!=0){close();return false;}
        return true;
    }
    bool ready() const {return handle_!=INVALID_HANDLE_VALUE;}
    void reset_energy() {energy_.reset();}
    Frame sample() {
        Frame frame{};
        if(!ready())return frame;
        const uint64_t start=GetTickCount64();
        uint64_t units=0,count=0,energy_time=0;
        bool first=true;
        for(DWORD_PTR bit=1;bit;bit<<=1){
            if(!(mask_&bit))continue;
            const DWORD_PTR old=SetThreadAffinityMask(GetCurrentThread(),bit);
            if(!old){energy_.reset();return Frame{};}
            uint64_t target=0,core=0,pkg=0;
            int t=0;
            bool ok=read(0x1a2,target)&&read(0x19c,core)&&temperature(target,core,t);
            if(ok&&first){
                ok=read(0x1b1,pkg)&&temperature(target,pkg,frame.package);
                if(ok && read(0x606,units)&&read(0x611,count))energy_time=GetTickCount64();
            }
            const bool restored=SetThreadAffinityMask(GetCurrentThread(),old)!=0;
            if(!ok||!restored){energy_.reset();return Frame{};}
            if(t>frame.hottest)frame.hottest=t;
            first=false;
        }
        frame.time_ms=start;
        if(first||GetTickCount64()-start>250){energy_.reset();return Frame{};}
        frame.valid=true;
        if(energy_time)
            frame.power_valid=energy_.update(energy_time,static_cast<uint32_t>(count),static_cast<unsigned>((units>>8)&31),frame.watts);
        else energy_.reset();
        return frame;
    }
private:
    bool read(uint32_t index,uint64_t& out) {
        switch(index){case 0x1a2:case 0x19c:case 0x1b1:case 0x606:case 0x611:break;default:return false;}
        struct Request {char name[32]; uint64_t index;};
        static_assert(sizeof(Request)==40,"PawnIO ABI");
        Request req{}; std::memcpy(req.name,"ioctl_read_msr",sizeof("ioctl_read_msr"));req.index=index;
        uint64_t value=0;DWORD returned=0;
        if(!DeviceIoControl(handle_,CTL_CODE(41394u,0x841u,METHOD_BUFFERED,FILE_ANY_ACCESS),
            &req,sizeof(req),&value,sizeof(value),&returned,nullptr)||returned!=sizeof(value))return false;
        out=value;return true;
    }
    HANDLE handle_=INVALID_HANDLE_VALUE;
    DWORD_PTR mask_=0;
    Energy energy_;
};
}
