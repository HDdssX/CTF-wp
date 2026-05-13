package org.springframework.boot.loader.net.protocol.jar;

import java.io.IOException;
import java.io.InputStream;

abstract class LazyDelegatingInputStream extends InputStream {
   private volatile InputStream in;

   public int read() throws IOException {
      return this.in().read();
   }

   public int read(byte[] b) throws IOException {
      return this.in().read(b);
   }

   public int read(byte[] b, int off, int len) throws IOException {
      return this.in().read(b, off, len);
   }

   public long skip(long n) throws IOException {
      return this.in().skip(n);
   }

   public int available() throws IOException {
      return this.in().available();
   }

   public boolean markSupported() {
      try {
         return this.in().markSupported();
      } catch (IOException var2) {
         return false;
      }
   }

   public synchronized void mark(int readlimit) {
      try {
         this.in().mark(readlimit);
      } catch (IOException var3) {
      }

   }

   public synchronized void reset() throws IOException {
      this.in().reset();
   }

   private InputStream in() throws IOException {
      InputStream in = this.in;
      if (in == null) {
         synchronized(this) {
            in = this.in;
            if (in == null) {
               in = this.getDelegateInputStream();
               this.in = in;
            }
         }
      }

      return in;
   }

   public void close() throws IOException {
      InputStream in = this.in;
      if (in != null) {
         synchronized(this) {
            in = this.in;
            if (in != null) {
               in.close();
            }
         }
      }

   }

   protected abstract InputStream getDelegateInputStream() throws IOException;
}
