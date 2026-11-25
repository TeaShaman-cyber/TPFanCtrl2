import ghidra.app.script.GhidraScript;
import ghidra.pcode.emu.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.pcode.exec.PcodeExecutorStatePiece.Reason;
import java.util.*;
public class R17Machine extends GhidraScript {
 final long base=0x20100,rec=0x11454,stop=0x14000;

 long number(byte[] a){long n=0;for(int i=a.length-1;i>=0;i--)n=(n<<8)|(a[i]&255);return n;}
 byte[] bytes(long v,int n){byte[] a=new byte[n];for(int i=0;i<n;i++)a[i]=(byte)(v>>>(8*i));return a;}
 class VM {
  PcodeEmulator emu;
  PcodeThread<byte[]> cpu;
  long romEnd,steps=0;
  int mmioReads=0,mmioWrites=0;
  long now=0; Map<Long,Long> deadlines=new HashMap<>();
  VM(int floor,int output)throws Exception{
   byte[] rom=new byte[(int)currentProgram.getMemory().getSize()];currentProgram.getMemory().getBytes(toAddr(0),rom);
   romEnd=base+rom.length;
   emu=new PcodeEmulator(currentProgram.getLanguage(),new PcodeEmulationCallbacks<byte[]>(){
    public void beforeLoad(PcodeThread<byte[]> t,PcodeOp op,AddressSpace s,byte[] off,int n){
     long a=number(off);guard(a,n,false);
     if(a==0x150e8&&n==2)t.getState().setVar(s,a,n,false,bytes(now,n));
     if(a>=0xfff440L&&a<0xfff4c0L)mmioReads++;
    }
    public void beforeStore(PcodeThread<byte[]> t,PcodeOp op,AddressSpace s,byte[] off,int n,byte[] value){
     long a=number(off);guard(a,n,true);
     if(a>=0xfff440L&&a<0xfff4c0L)mmioWrites++;
    }
   });
   emu.getSharedState().setConcrete(toAddr(base),rom);
   for(long[] r:new long[][]{{rec,0xb0},{0x12c90,16},{0x14000,256},{0x11058,2},{0xfff440,128},{0xfffe0e,2},{0x12d62,1},{0x150e8,2},{0xfff340,0x110}})
    emu.getSharedState().setConcrete(toAddr(r[0]),new byte[(int)r[1]]);
   cpu=emu.newThread();
   for(String n:new String[]{"R0","R1","R2","R3","R4","R5","R6","R7","R8","R9","R10","R11","R12","R13","SP","RA","PSR"})
    if(currentProgram.getRegister(n)!=null)reg(n,0);
   put(rec,2,1);put(rec+7,1,11);put(rec+0xc,1,8);put(rec+0xac,1,8);put(rec+0x1c,2,500);put(rec+0x1e,2,floor);put(rec+0x20,2,output);put(rec+0x16,2,3950);put(rec+0x10,2,65535);
   put(0x12c90,2,1);put(0xfff446,2,output-1);put(0xfff444,1,0x80);put(0x11058,2,1);
  }
  boolean inside(long a,int n,long lo,long hi){return a>=lo&&a+n<=hi;}
  void guard(long a,int n,boolean write){
   if(!write&&inside(a,n,base,romEnd))return;
   for(long[] r:new long[][]{{rec,rec+0xb0},{0x12c90,0x12ca0},{0x14000,0x14100},{0x11058,0x1105a},{0xfff440,0xfff4c0},{0xfffe0e,0xfffe10},{0x12d62,0x12d63},{0x150e8,0x150ea},{0xfff340,0xfff450}})
    if(inside(a,n,r[0],r[1]))return;
   throw new IllegalStateException("UNMODELED "+(write?"write":"read")+" "+Long.toHexString(a)+" size="+n+" pc="+cpu.getCounter());
  }
  void put(long a,int n,int v){emu.getSharedState().setConcrete(toAddr(a),bytes(v,n));}
  int get(long a,int n){return (int)number(emu.getSharedState().inspectConcrete(toAddr(a),n));}
  void reg(String name,long v){var r=currentProgram.getRegister(name);cpu.getState().setVar(r,bytes(v,r.getMinimumByteSize()));}
  long reg(String name){return number(cpu.getState().getVar(currentProgram.getRegister(name),Reason.INSPECT));}
  void call(long offset,int arg)throws Exception{
   reg("SP",0x14100);reg("RA",stop/2);reg("R2",arg);reg("PSR",0);
   cpu.overrideCounter(toAddr(base+offset));cpu.overrideContextWithDefault();
   int n=0;
   while(cpu.getCounter().getOffset()!=stop&&n++<2000){
    long p=cpu.getCounter().getOffset();
    if(p==0x16882L||p==0x16a62L||p==0x164c4L){
     long id=reg("R2")&65535;
     if(p==0x16882L){long delay=reg("R3")&65535;deadlines.put(id,now+delay);println("TIMER_SET id="+id+" delay="+delay+" now="+now);}
     else if(p==0x16a62L){if(!deadlines.containsKey(id))throw new Exception("unknown timer "+id);reg("R0",now>=deadlines.get(id)?1:0);println("TIMER_READY id="+id+" now="+now+" deadline="+deadlines.get(id));}
     else println("ROM_NOTIFY id="+id+" now="+now);
     cpu.overrideCounter(toAddr(reg("RA")*2));continue;
    }
    if(p<base||p>=romEnd)throw new IllegalStateException("UNMODELED PC "+Long.toHexString(p)+" RA="+Long.toHexString(reg("RA")));
    cpu.stepInstruction();steps++;
   }
   if(cpu.getCounter().getOffset()!=stop)throw new Exception("step budget");
  }
  void tick(String s,int stage,int sub,int floor,int output)throws Exception{
   call(0x190da,24);
   println("TICK "+s+" stage="+get(rec+7,1)+" sub="+get(rec+0xc,1)+" floor="+get(rec+0x1e,2)+" output="+get(rec+0x20,2)+" steps="+steps+" mmio="+mmioReads+"/"+mmioWrites);
   if(get(rec+7,1)!=stage||get(rec+0xc,1)!=sub||get(rec+0x1e,2)!=floor||get(rec+0x20,2)!=output)throw new Exception("state mismatch "+s);
  }
 }
 public void run()throws Exception{
  var control=new VM(25,400);
  control.put(rec+0xac,1,7);
  control.tick("eighth-invalid",11,0,25,400);
  if(control.get(rec+0xac,1)!=8)throw new Exception("miss counter");
  var vm=new VM(25,400);
  vm.tick("ninth-invalid",12,0,25,400);
  if(vm.get(rec+0xac,1)!=9)throw new Exception("miss counter");
  vm.tick("raise",12,1,401,400);
  vm.tick("disable",12,2,401,400);
  if((vm.get(0xfff444,1)&0x80)!=0)throw new Exception("PWM not disabled");
  vm.tick("schedule",12,3,401,400);
  if(!Long.valueOf(500).equals(vm.deadlines.get(24L)))throw new Exception("timer");
  vm.tick("wait",12,3,401,400);
  vm.now=499;vm.tick("before-deadline",12,3,401,400);
  vm.now=500;vm.tick("deadline",12,4,401,400);
  vm.tick("recover",6,0,401,400);
  vm.tick("restart",6,1,401,500);
  if(vm.get(0xfff446,2)!=499||(vm.get(0xfff444,1)&0x80)==0)throw new Exception("PWM not restarted");
  vm.tick("restart-deadline",6,2,401,500);
  if(vm.get(rec+0x46,2)!=2500)throw new Exception("restart deadline");
  vm.tick("null-dispatch",7,0,401,500);
  try{vm.guard(0xff0000,1,false);throw new Exception("unknown MMIO allowed");}
  catch(IllegalStateException expected){println("UNMODELED_GUARD_PASS "+expected.getMessage());}
  println("R17_DISPATCH_PASS original indirect dispatcher with relocated ROM; virtual clock");
 }
}
