import ghidra.app.script.GhidraScript;
import ghidra.pcode.emu.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.pcode.exec.PcodeExecutorStatePiece.Reason;
import java.util.*;
public class R17Return extends GhidraScript {
 final long base=0x20100,rec=0x11454,stop=0x14000;

 long number(byte[] a){long n=0;for(int i=a.length-1;i>=0;i--)n=(n<<8)|(a[i]&255);return n;}
 byte[] bytes(long v,int n){byte[] a=new byte[n];for(int i=0;i<n;i++)a[i]=(byte)(v>>>(8*i));return a;}
 class VM {
  PcodeEmulator emu;
  PcodeThread<byte[]> cpu;
  long romEnd,steps=0;
  int mmioReads=0,mmioWrites=0; int capture=0,event=0,captureReads=0,clearWrites=0;
  long now=0; Map<Long,Long> deadlines=new HashMap<>();
  VM(int floor,int output)throws Exception{
   byte[] rom=new byte[(int)currentProgram.getMemory().getSize()];currentProgram.getMemory().getBytes(toAddr(0),rom);
   romEnd=base+rom.length;
   emu=new PcodeEmulator(currentProgram.getLanguage(),new PcodeEmulationCallbacks<byte[]>(){
    public void beforeLoad(PcodeThread<byte[]> t,PcodeOp op,AddressSpace s,byte[] off,int n){
     long a=number(off);guard(a,n,false);
     if(a==0xfff342&&n==2){captureReads++;t.getState().setVar(s,a,n,false,bytes(capture,n));}
     if(a==0xfff34e&&n==1)t.getState().setVar(s,a,n,false,bytes(event,n));
     if(a==0x150e8&&n==2)t.getState().setVar(s,a,n,false,bytes(now,n));
     if(a>=0xfff440L&&a<0xfff4c0L)mmioReads++;
    }
    public void beforeStore(PcodeThread<byte[]> t,PcodeOp op,AddressSpace s,byte[] off,int n,byte[] value){
     long a=number(off);guard(a,n,true);
     if(a==0xfff350&&n==1){clearWrites++;event &= ~(int)number(value);}
     if(a>=0xfff440L&&a<0xfff4c0L)mmioWrites++;
    }
   });
   emu.getSharedState().setConcrete(toAddr(base),rom);
   for(long[] r:new long[][]{{rec,0xb0},{0x12c90,16},{0x14000,256},{0x11058,2},{0xfff440,128},{0xfffe0e,2},{0x12d62,1},{0x150e8,2},{0x138a0,2},{0xfff340,0x110}})
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
   for(long[] r:new long[][]{{rec,rec+0xb0},{0x12c90,0x12ca0},{0x14000,0x14100},{0x11058,0x1105a},{0xfff440,0xfff4c0},{0xfffe0e,0xfffe10},{0x12d62,0x12d63},{0x150e8,0x150ea},{0x138a0,0x138a2},{0xfff340,0xfff450}})
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
    if(p==0x16882L||p==0x16a62L||p==0x164c4L||p==0x1643cL||p==0x16aaaL){
     long id=reg("R2")&65535;
     if(p==0x16882L){long delay=reg("R3")&65535;deadlines.put(id,now+delay);println("TIMER_SET id="+id+" delay="+delay+" now="+now);}
     else if(p==0x16a62L){if(!deadlines.containsKey(id))throw new Exception("unknown timer "+id);reg("R0",now>=deadlines.get(id)?1:0);println("TIMER_READY id="+id+" now="+now+" deadline="+deadlines.get(id));}
     else if(p==0x16aaaL){int delta=(short)((id-now)&65535);reg("R0",delta);println("DEADLINE remaining="+delta);}
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
 void expect(boolean ok,String name)throws Exception{if(!ok)throw new Exception(name);println("PASS "+name);}
 void state(VM v,String label){println("STATE "+label+" t="+v.now+" stage="+v.get(rec+7,1)+" sub="+v.get(rec+0xc,1)+" rpm="+v.get(rec+0x10,2)+" misses="+v.get(rec+0xac,1)+" floor="+v.get(rec+0x1e,2)+" output="+v.get(rec+0x20,2));}
 void pulse(VM v,int period)throws Exception{v.capture=65535-period;v.event=1;v.call(0xf0fe,1);expect(v.event==0,"capture event cleared");}
 VM init()throws Exception{
  var v=new VM(25,400);
  v.put(rec,2,0);v.put(rec+7,1,11);v.put(rec+0xc,1,3);v.put(rec+0xac,1,0);
  v.put(rec+8,1,5);v.put(rec+9,1,5);v.put(rec+10,1,5);v.put(rec+11,1,3);
  v.put(rec+0x94,4,0x5876e);v.put(rec+0x48,2,2000);v.put(rec+0x44,2,250);v.put(rec+3,1,24);v.put(rec+0xe,1,2);v.put(0x12d62,1,0);
  v.put(0xfff34c,1,0x20);
  return v;
 }
 void dispatch(VM v)throws Exception{v.call(0x190da,24);}
 void sample(VM v,int period)throws Exception{
  expect(v.get(rec+0xc,1)==3,"acquisition entry");
  dispatch(v);
  expect(v.get(rec+0xc,1)==4,"acquisition armed");
  if(period>0){pulse(v,period);pulse(v,period);}
  v.now+=100;
  dispatch(v);dispatch(v);dispatch(v);state(v,"converted");
  expect(v.get(rec+0xc,1)==7,"conversion completed");
  expect(v.get(rec+0x10,2)==(period>0?60000000/period:65535),"converted input");
  dispatch(v);dispatch(v);state(v,"validated");
 }
 void next(VM v)throws Exception{
  dispatch(v);dispatch(v);v.now+=250;dispatch(v);
  state(v,"next acquisition");
 }
 public void run()throws Exception{
  var v=init();
  sample(v,12000);
  expect(v.get(rec+7,1)==11&&v.get(rec+0xac,1)==0,"valid stays normal");
  next(v);
  for(int i=1;i<=9;i++){
   sample(v,0);
   expect(v.get(rec+0xac,1)==i,"miss count "+i);
   expect(v.get(rec+7,1)==(i<9?11:12),"stage after miss "+i);
   if(i<9)next(v);
  }
  int output=v.get(rec+0x20,2);
  v.tick("raise",12,1,output+1,output);
  v.tick("disable",12,2,output+1,output);
  expect((v.get(0xfff444,1)&128)==0,"PWM disabled");
  v.tick("schedule",12,3,output+1,output);
  v.now+=499;v.tick("before deadline",12,3,output+1,output);
  v.now++;v.tick("deadline",12,4,output+1,output);
  v.tick("recover",6,0,output+1,output);
  v.tick("restart",6,1,output+1,500);
  expect(v.get(0xfff446,2)==499&&(v.get(0xfff444,1)&128)!=0,"PWM restarted at maximum");
  v.tick("restart deadline",6,2,output+1,500);
  v.tick("stage7",7,0,output+1,500);
  for(int i=0;i<100;i++){
   int stage=v.get(rec+7,1),sub=v.get(rec+0xc,1);
   if(stage==11&&sub==0){state(v,"returned");break;}
   dispatch(v);state(v,"return step "+i);
   if((stage==7&&sub==0)||(stage==9&&sub==2)){
    for(int j=0;j<5;j++){
     v.capture=65535-12000;v.event=1;v.call(0xf0fe,1);
     println("RESTART_CAPTURE event="+v.event+" idx="+v.get(rec+0x38,1)+" d="+v.get(rec+0xd,1)+" driver="+v.get(0x12d62,1));
     // Outer IRQ wrapper clears remaining status (original f27c), modeled here.
     v.event=0;
    }
    v.now+=100;
   }
   if(stage==9&&sub==0)v.now=Math.max(v.now,v.deadlines.getOrDefault(24L,v.now));
   if(stage==7&&sub==3)v.now+=2000;
   if(i==99)throw new Exception("return budget");
  }
  expect(v.get(rec+7,1)==11,"return to regulation");
  expect(v.get(rec+0x16,2)==3950&&v.get(rec+0xac,1)==0,"normal target and cleared misses");
  expect(v.get(rec+0x1e,2)==381&&v.get(rec+0x20,2)==381,"raised floor survives complete return");
  for(int k=0;k<6;k++){
   next(v);sample(v,12000);
   expect(v.get(rec+7,1)==11&&v.get(rec+0xac,1)==0&&v.get(rec+0x10,2)==5000&&v.get(rec+0x20,2)==381&&v.get(rec+0x1e,2)==381,"valid overspeed remains floor limited "+k);
  }
  var c=init();
  for(int i=1;i<=8;i++){sample(c,0);expect(c.get(rec+0xac,1)==i&&c.get(rec+7,1)==11,"control miss "+i);next(c);}
  sample(c,12000);
  expect(c.get(rec+7,1)==11&&c.get(rec+0xac,1)==0&&c.get(rec+0x1e,2)==25,"valid signal resets consecutive misses");
  next(c);sample(c,0);
  expect(c.get(rec+7,1)==11&&c.get(rec+0xac,1)==1,"next miss starts new streak");
  var normal=init();
  sample(normal,12000);
  for(int k=0;k<6;k++){next(normal);sample(normal,12000);}
  expect(normal.get(rec+0x1e,2)==25&&normal.get(rec+0x20,2)<381&&normal.get(rec+7,1)==11,"no-fault control can decrease output");
  state(normal,"no-fault control");
  println("RETURN_SIGNAL_PASS");
 }
}
