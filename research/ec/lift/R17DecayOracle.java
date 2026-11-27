import ghidra.app.script.GhidraScript;
import ghidra.app.plugin.assembler.Assemblers;
import ghidra.pcode.emu.*;
import ghidra.program.model.address.*;
import ghidra.program.model.pcode.PcodeOp;
import ghidra.pcode.exec.PcodeExecutorStatePiece.Reason;
import java.util.*;
public class R17DecayOracle extends GhidraScript {
 final long base=0x20100,rec=0x11454,stop=0x14000;
 boolean candidate=true;
 final long stub=0x3a000, tail=0x3a080;
 byte[] bal(long from,long to){
  long d=to-from;
  if((d&1)!=0||d< -0x800000||d>0x7ffffe)throw new IllegalArgumentException("BAL range");
  return new byte[]{(byte)(d>>16),(byte)0xc0,(byte)d,(byte)(d>>8)};
 }
 byte[] stubCode()throws Exception{
  byte[] code=new byte[0x90];var a=Assemblers.getAssembler(currentProgram);
  long pc=stub;
  String[] lines={
   "push $0x2, RA_L",
   "LOADB *0x7(R3R2),R0","CMPB $0xb,R0","BRne *0x0003a080",
   "LOADB *0xc(R3R2),R0","CMPB $0x0,R0","BRne *0x0003a080",
   "LOADB *0xac(R3R2),R0","CMPB $0x0,R0","BRne *0x0003a080",
   "LOADW *0x1c(R3R2),R0","CMPW $0x1f4,R0","BRne *0x0003a080",
   "LOADW *0x1e(R3R2),R1","CMPW $0x19,R1","BRhs *0x0003a080",
   "CMPW $0x1f4,R1","BRlo *0x0003a080",
   "LOADW *0x20(R3R2),R0","CMPW R1,R0","BRne *0x0003a080",
   "CMPW R1,R4","BRls *0x0003a080",
   "LOADW *0x16(R3R2),R0","CMPW $0x0,R0","BReq *0x0003a080",
   "CMPW $0x2710,R0","BRlo *0x0003a080",
   "ADDW $0x64,R0","LOADW *0x10(R3R2),R5","CMPW $-0x1,R5","BReq *0x0003a080",
   "CMPW R0,R5","BRhs *0x0003a080",
   "SUBW $0x1,R1","STORW R1,*0x1e(R3R2)",
   "BR *0x0003a080"
  };
  for(String l:lines){byte[] b=a.assembleLine(toAddr(pc),l);if(pc+b.length>tail)throw new Exception("stub overflow");System.arraycopy(b,0,code,(int)(pc-stub),b.length);println("ASM "+Long.toHexString(pc)+" "+l+" "+HexFormat.of().formatHex(b));pc+=b.length;}
  byte[] b=bal(tail,0x19afa);System.arraycopy(b,0,code,(int)(tail-stub),b.length);
  b=a.assembleLine(toAddr(tail+4),"popret $0x2, RA_L");System.arraycopy(b,0,code,(int)(tail+4-stub),b.length);
  return code;
 }

 long number(byte[] a){long n=0;for(int i=a.length-1;i>=0;i--)n=(n<<8)|(a[i]&255);return n;}
 byte[] bytes(long v,int n){byte[] a=new byte[n];for(int i=0;i<n;i++)a[i]=(byte)(v>>>(8*i));return a;}
 class VM {
  PcodeEmulator emu;
  PcodeThread<byte[]> cpu;
  long romEnd,steps=0; int clampVisits=0,stubVisits=0;
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
   if(candidate){
    byte[] code=stubCode();emu.getSharedState().setConcrete(toAddr(base+stub),code);
    emu.getSharedState().setConcrete(toAddr(base+0x19974),bal(0x19974,stub));romEnd=base+stub+code.length;
   }
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
    long p=cpu.getCounter().getOffset(); if(p==base+stub)stubVisits++; if(p==base+0x19974 || p==base+0x19892 || p==base+0x19afa){clampVisits++;println("CLAMP_PC "+Long.toHexString(p-base)+" R4="+reg("R4")+" stage="+get(rec+7,1)+" sub="+get(rec+0xc,1));}
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
  int selection(int[] x)throws Exception{
   put(rec+7,1,x[0]);put(rec+0xc,1,x[1]);put(rec+0xac,1,x[2]);
   put(rec+0x1e,2,x[3]);put(rec+0x1c,2,x[4]);put(rec+0x20,2,x[5]);
   put(rec+0x16,2,x[7]);put(rec+0x10,2,x[8]);
   reg("R2",rec&65535);reg("R3",rec>>>16);reg("R4",x[6]);reg("R0",x[9]);reg("PSR",x[10]);
   cpu.overrideCounter(toAddr(base+0x3a002));cpu.overrideContextWithDefault();
   int n=0;
   while(cpu.getCounter().getOffset()!=base+0x3a080 && n++<80){
    long pc=cpu.getCounter().getOffset()-base;
    if(pc<0x3a002||pc>=0x3a07a)throw new Exception("decay escaped");
    cpu.stepInstruction();
   }
   if(cpu.getCounter().getOffset()!=base+0x3a080)throw new Exception("decay budget");
   if(get(rec+7,1)!=x[0]||get(rec+0xc,1)!=x[1]||get(rec+0xac,1)!=x[2]||get(rec+0x20,2)!=x[5]||reg("R4")!=x[6])throw new Exception("unexpected effect");
   return get(rec+0x1e,2);
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



 VM fixture(int floor,int output)throws Exception{
  var v=init();v.put(rec+0x1e,2,floor);v.put(rec+0x20,2,output);return v;
 }
 void samples(VM v,int period,int count)throws Exception{
  for(int k=0;k<count;k++){if(k>0)next(v);sample(v,period);}
 }
 public void run()throws Exception{
  candidate=true;var v=init();var rng=new Random(289);
  int[][] vals={{0,10,11,12,255},{0,1,255},{0,1,8,9,127,255},{0,24,25,26,499,500,501,65535},{0,499,500,501,65535},{0,25,499,500,501,65535},{0,24,25,499,500,501,65535},{0,1,2550,9999,10000,10001,65535},{0,299,1141,2550,2649,2650,2651,5000,65534,65535}};
  int[] good={11,0,0,500,500,500,499,2550,5000,0,0};
  var rows=new ArrayList<int[]>(); rows.add(good.clone());
  for(int j=0;j<vals.length;j++)for(int value:vals[j]){
    int[] x=good.clone();x[j]=value;
    if(j==3){x[5]=value;x[6]=Math.max(0,value-1);}
    x[9]=rng.nextInt(65536);x[10]=rng.nextInt(65536);rows.add(x);
  }
  while(rows.size()<512){
    int[] x=good.clone();
    if(rows.size()%3==0){
      x[3]=26+rng.nextInt(475);x[5]=x[3];x[6]=rng.nextInt(x[3]);x[7]=1+rng.nextInt(10000);x[8]=Math.min(65534,x[7]+101+rng.nextInt(3000));
    }else for(int j=0;j<vals.length;j++)if(rng.nextInt(4)==0)x[j]=vals[j][rng.nextInt(vals[j].length)];
    x[9]=rng.nextInt(65536);x[10]=rng.nextInt(65536);rows.add(x);
  }
  for(int[] x:rows){int r=v.selection(x);var b=new StringBuilder("ORACLE");for(int i:x)b.append(" ").append(i);println(b+" "+r);}
  println("ORACLE_PASS "+rows.size());
 }
}
