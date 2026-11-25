"""Compile the actual trace dispatch with fake UI ownership, no EC access."""
from pathlib import Path
import subprocess,tempfile
src=(Path(__file__).resolve().parents[1]/'fancontrol/misc.cpp').read_text(encoding='utf-8-sig')
def fn(name):
 a=src.index('FANCONTROL::'+name+'(')
 b=src.index('{',a);i=b+1;d=1
 while d:
  d+=(src[i]=='{')-(src[i]=='}');i+=1
 return 'void '+src[a:i]
body=fn('Trace')
if 'FANCONTROL::DrainTrace()' in src:body+=fn('DrainTrace')
else:body+='void FANCONTROL::DrainTrace() {}'
pre=r"""
#include <cstdio>
#include <cstring>
#include <cstdarg>
#include <deque>
#include <string>
#include <mutex>
#include <vector>
using std::size_t;
using LONG=long;using DWORD=unsigned long;
using errno_t=int;
#define ARRAYMAX(x) (sizeof(x)/sizeof(x[0]))
#define _TRUNCATE 0
DWORD current=1;
DWORD GetCurrentThreadId(){return current;}
LONG InterlockedIncrement(LONG* p){return ++*p;}
int sprintf_s(char* p,size_t n,const char* fmt,...){va_list a;va_start(a,fmt);int v=vsnprintf(p,n,fmt,a);va_end(a);return v;}
template<size_t N> void strcpy_s(char (&p)[N],size_t n,const char* s){snprintf(p,n,"%s",s);}
void strncpy_s(char* p,size_t n,const char* s,int){snprintf(p,n,"%s",s);}
int fopen_s(FILE** f,const char*,const char*){*f=nullptr;return 1;}
struct FCSHARED{LONG traceSeq=0;char traceLines[48][160]{};} ring;
FCSHARED* SharedState(){return &ring;}
bool g_clientMode=false;
class FANCONTROL {
public:
 int hwndDialog=1,Log2File=0,wrongThread=0;
 const DWORD TraceOwnerThread=GetCurrentThreadId();
 std::mutex TraceQueueMutex;
 std::deque<std::string> TraceQueue;
 std::vector<std::string> shown;
 void CurrentDateTimeLocalized(char* p,size_t n){snprintf(p,n,"T");}
 void Trace(const char*);
 void DrainTrace();
 void TraceAppend(const char* s){if(current!=TraceOwnerThread)++wrongThread;shown.emplace_back(s);}
};
"""
main=r"""
int main(){
 int failures=0;
 auto check=[&](bool ok,const char* n){printf("%s %s\n",ok?"PASS":"FAIL",n);failures+=!ok;};
 FANCONTROL f;
 current=2;f.Trace("worker failure");
 check(f.wrongThread==0&&f.shown.empty(),"worker returns without synchronous UI call");
 check(ring.traceSeq==1&&strstr(ring.traceLines[1],"worker failure"),"worker still publishes diagnostic");
 current=1;f.DrainTrace();
 check(f.shown.size()==1&&f.shown[0].find("worker failure")!=std::string::npos,"owner drains worker line");
 f.DrainTrace();check(f.shown.size()==1,"no duplicate drain");
 current=2;f.Trace("before close");current=1;f.Trace("close");
 check(f.shown.size()==3&&f.shown[1].find("before close")!=std::string::npos&&f.shown[2].find("close")!=std::string::npos,"owner trace preserves queue order");
 current=2;for(int i=0;i<150;i++)f.Trace("burst");
 check(f.TraceQueue.size()==100,"bounded worker backlog");
 current=1;f.DrainTrace();check(f.TraceQueue.empty()&&f.wrongThread==0,"burst drained on owner");
 return failures?1:0;
}
"""
with tempfile.TemporaryDirectory() as d:
 p=Path(d)/'trace.cpp';p.write_text(pre+body+main)
 subprocess.run(['g++','-std=c++17','-pthread',str(p),'-o',str(p.with_suffix(''))],check=True)
 raise SystemExit(subprocess.run([str(p.with_suffix(''))]).returncode)
