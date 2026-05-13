package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.util.Collection;
import java.util.Iterator;
import java.util.List;

class VirtualDataBlock implements DataBlock {
   private List<DataBlock> parts;
   private long size;

   protected VirtualDataBlock() {
   }

   VirtualDataBlock(Collection<? extends DataBlock> parts) throws IOException {
      this.setParts(parts);
   }

   protected void setParts(Collection<? extends DataBlock> parts) throws IOException {
      this.parts = List.copyOf(parts);
      long size = 0L;

      DataBlock part;
      for(Iterator var4 = parts.iterator(); var4.hasNext(); size += part.size()) {
         part = (DataBlock)var4.next();
      }

      this.size = size;
   }

   public long size() throws IOException {
      return this.size;
   }

   public int read(ByteBuffer dst, long pos) throws IOException {
      if (pos >= 0L && pos < this.size) {
         long offset = 0L;
         int result = 0;

         DataBlock part;
         int count;
         for(Iterator var7 = this.parts.iterator(); var7.hasNext(); offset += part.size()) {
            for(part = (DataBlock)var7.next(); pos >= offset && pos < offset + part.size(); pos += (long)count) {
               count = part.read(dst, pos - offset);
               result += Math.max(count, 0);
               if (count <= 0 || !dst.hasRemaining()) {
                  return result;
               }
            }
         }

         return result;
      } else {
         return -1;
      }
   }
}
