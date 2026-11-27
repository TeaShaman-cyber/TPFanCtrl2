import ghidra.app.script.GhidraScript;
import ghidra.program.model.pcode.*;
public class ExtractDispatcher extends GhidraScript {
 String v(Varnode n) {return n==null?"-":n.getAddress().getAddressSpace().getName()+":"+Long.toHexString(n.getOffset())+":"+n.getSize();}
 public void run() throws Exception {
  long pc=0x190daL;
  while(pc<0x191e2L){
   var a=toAddr(pc); if(!disassemble(a))throw new Exception("decode "+a);
   var i=getInstructionAt(a);if(i==null)throw new Exception("missing instruction");
   println("INS "+Long.toHexString(pc)+" "+i.getLength()+" "+i);
   for(var p:i.getPcode()){String line="OP "+p.getMnemonic()+" "+v(p.getOutput());for(var n:p.getInputs())line+=" "+v(n);println(line);}
   pc+=i.getLength();
  }
  if(pc!=0x191e2L)throw new Exception("end mismatch");
  for(long a=0x55248;a<0x553dc;a+=4){
   println("TABLE "+Long.toHexString(a)+" "+Long.toHexString(Integer.toUnsignedLong(currentProgram.getMemory().getInt(toAddr(a-0x20100)))));
  }
  println("EXTRACT_PASS");
 }
}
