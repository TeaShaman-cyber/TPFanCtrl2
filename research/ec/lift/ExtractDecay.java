import ghidra.app.script.GhidraScript;
import ghidra.program.model.pcode.*;
public class ExtractDecay extends GhidraScript {
 String v(Varnode n) {return n==null?"-":n.getAddress().getAddressSpace().getName()+":"+Long.toHexString(n.getOffset())+":"+n.getSize();}
 public void run() throws Exception {
  long pc=0x3a002L;
  while(pc<0x3a07aL){
   var a=toAddr(pc); if(!disassemble(a))throw new Exception("decode "+a);
   var i=getInstructionAt(a);if(i==null)throw new Exception("missing instruction");
   println("INS "+Long.toHexString(pc)+" "+i.getLength()+" "+i);
   for(var p:i.getPcode()){String line="OP "+p.getMnemonic()+" "+v(p.getOutput());for(var n:p.getInputs())line+=" "+v(n);println(line);}
   pc+=i.getLength();
  }
  if(pc!=0x3a07aL)throw new Exception("end mismatch");
  println("EXTRACT_PASS");
 }
}
