package org.springframework.boot.loader.net.protocol.nested;

import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import org.springframework.boot.loader.zip.CloseableDataBlock;
import org.springframework.boot.loader.zip.ZipContent;

class NestedUrlConnectionResources implements Runnable {
   private final NestedLocation location;
   private volatile ZipContent zipContent;
   private volatile long size = -1L;
   private volatile InputStream inputStream;

   NestedUrlConnectionResources(NestedLocation location) {
      this.location = location;
   }

   NestedLocation getLocation() {
      return this.location;
   }

   void connect() throws IOException {
      synchronized(this) {
         if (this.zipContent == null) {
            this.zipContent = ZipContent.open(this.location.path(), this.location.nestedEntryName());

            try {
               this.connectData();
            } catch (RuntimeException | IOException var4) {
               this.zipContent.close();
               this.zipContent = null;
               throw var4;
            }
         }

      }
   }

   private void connectData() throws IOException {
      CloseableDataBlock data = this.zipContent.openRawZipData();

      try {
         this.size = data.size();
         this.inputStream = data.asInputStream();
      } catch (RuntimeException | IOException var3) {
         data.close();
      }

   }

   InputStream getInputStream() throws IOException {
      synchronized(this) {
         if (this.inputStream == null) {
            throw new IOException("Nested location not found " + this.location);
         } else {
            return this.inputStream;
         }
      }
   }

   long getContentLength() {
      return this.size;
   }

   public void run() {
      this.releaseAll();
   }

   private void releaseAll() {
      synchronized(this) {
         if (this.zipContent != null) {
            IOException exceptionChain = null;

            try {
               this.inputStream.close();
            } catch (IOException var6) {
               exceptionChain = this.addToExceptionChain(exceptionChain, var6);
            }

            try {
               this.zipContent.close();
            } catch (IOException var5) {
               exceptionChain = this.addToExceptionChain(exceptionChain, var5);
            }

            this.size = -1L;
            if (exceptionChain != null) {
               throw new UncheckedIOException(exceptionChain);
            }
         }

      }
   }

   private IOException addToExceptionChain(IOException exceptionChain, IOException ex) {
      if (exceptionChain != null) {
         exceptionChain.addSuppressed(ex);
         return exceptionChain;
      } else {
         return ex;
      }
   }
}
