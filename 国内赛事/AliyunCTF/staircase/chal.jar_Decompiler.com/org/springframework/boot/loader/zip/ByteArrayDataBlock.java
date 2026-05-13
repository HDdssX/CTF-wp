package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;

class ByteArrayDataBlock implements CloseableDataBlock {
   private final byte[] bytes;

   ByteArrayDataBlock(byte... bytes) {
      this.bytes = bytes;
   }

   public long size() throws IOException {
      return (long)this.bytes.length;
   }

   public int read(ByteBuffer dst, long pos) throws IOException {
      return this.read(dst, (int)pos);
   }

   private int read(ByteBuffer dst, int pos) {
      int remaining = dst.remaining();
      int length = Math.min(this.bytes.length - pos, remaining);
      dst.put(this.bytes, pos, length);
      return length;
   }

   public void close() throws IOException {
   }
}
