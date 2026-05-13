package org.springframework.boot.loader.zip;

import java.io.Closeable;
import java.io.IOException;
import java.io.InputStream;
import java.nio.ByteBuffer;

class DataBlockInputStream extends InputStream {
   private final DataBlock dataBlock;
   private long pos;
   private long remaining;
   private volatile boolean closed;

   DataBlockInputStream(DataBlock dataBlock) throws IOException {
      this.dataBlock = dataBlock;
      this.remaining = dataBlock.size();
   }

   public int read() throws IOException {
      byte[] b = new byte[1];
      return this.read(b, 0, 1) == 1 ? b[0] & 255 : -1;
   }

   public int read(byte[] b, int off, int len) throws IOException {
      this.ensureOpen();
      ByteBuffer dst = ByteBuffer.wrap(b, off, len);
      int count = this.dataBlock.read(dst, this.pos);
      if (count > 0) {
         this.pos += (long)count;
         this.remaining -= (long)count;
      }

      return count;
   }

   public long skip(long n) throws IOException {
      long count = n > 0L ? this.maxForwardSkip(n) : this.maxBackwardSkip(n);
      this.pos += count;
      this.remaining -= count;
      return count;
   }

   private long maxForwardSkip(long n) {
      boolean willCauseOverflow = this.pos + n < 0L;
      return !willCauseOverflow && n <= this.remaining ? n : this.remaining;
   }

   private long maxBackwardSkip(long n) {
      return Math.max(-this.pos, n);
   }

   public int available() {
      if (this.closed) {
         return 0;
      } else {
         return this.remaining < 2147483647L ? (int)this.remaining : Integer.MAX_VALUE;
      }
   }

   private void ensureOpen() throws IOException {
      if (this.closed) {
         throw new IOException("InputStream closed");
      }
   }

   public void close() throws IOException {
      if (!this.closed) {
         this.closed = true;
         DataBlock var2 = this.dataBlock;
         if (var2 instanceof Closeable) {
            Closeable closeable = (Closeable)var2;
            closeable.close();
         }

      }
   }
}
