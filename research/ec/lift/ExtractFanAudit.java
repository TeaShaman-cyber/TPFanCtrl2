import ghidra.app.script.GhidraScript;
import ghidra.program.model.pcode.*;
public class ExtractFanAudit extends GhidraScript {
 String v(Varnode n) {return n==null?"-":n.getAddress().getAddressSpace().getName()+":"+Long.toHexString(n.getOffset())+":"+n.getSize();}
 public void run() throws Exception {
  for(long[] range:new long[][]{{0x192e6,0x19356},{0x199aa,0x19a08},{0x19d56,0x19daa}}){
  println("RANGE "+Long.toHexString(range[0])+" "+Long.toHexString(range[1]));
  long pc=range[0];
  while(pc<range[1]){
   var a=toAddr(pc); if(!disassemble(a))throw new Exception("decode "+a);
   var i=getInstructionAt(a);if(i==null)throw new Exception("missing instruction");
   println("INS "+Long.toHexString(pc)+" "+i.getLength()+" "+i);
   for(var p:i.getPcode()){String line="OP "+p.getMnemonic()+" "+v(p.getOutput());for(var n:p.getInputs())line+=" "+v(n);println(line);}
   pc+=i.getLength();
  }
  if(pc!=range[1])throw new Exception("end mismatch");
  }
  println("EXTRACT_PASS");
 }
}
