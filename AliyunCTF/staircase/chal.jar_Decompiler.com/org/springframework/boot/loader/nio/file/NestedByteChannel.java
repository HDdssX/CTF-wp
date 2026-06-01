package org.springframework.boot.loader.nio.file;

import java.io.IOException;
import java.io.UncheckedIOException;
import java.lang.ref.Cleaner.Cleanable;
import java.nio.ByteBuffer;
import java.nio.channels.ClosedChannelException;
import java.nio.channels.NonWritableChannelException;
import java.nio.channels.SeekableByteChannel;
import java.nio.file.Path;
import org.springframework.boot.loader.ref.Cleaner;
import org.springframework.boot.loader.zip.CloseableDataBlock;
import org.springframework.boot.loader.zip.DataBlock;
import org.springframework.boot.loader.zip.ZipContent;

class NestedByteChannel implements SeekableByteChannel {
   private long position;
   private final NestedByteChannel.Resources resources;
   private final Cleanable cleanup;
   private final long size;
   private volatile boolean closed;

   NestedByteChannel(Path path, String nestedEntryName) throws IOException {
      this(path, nestedEntryName, Cleaner.instance);
   }

   NestedByteChannel(Path path, String nestedEntryName, Cleaner cleaner) throws IOException {
      this.resources = new NestedByteChannel.Resources(path, nestedEntryName);
      this.cleanup = cleaner.register(this, this.resources);
      this.size = this.resources.getData().size();
   }

   public boolean isOpen() {
      return !this.closed;
   }

   public void close() throws IOException {
      if (!this.closed) {
         this.closed = true;

         try {
            this.cleanup.clean();
         } catch (UncheckedIOException var2) {
            throw var2.getCause();
         }
      }
   }

   public int read(ByteBuffer dst) throws IOException {
      this.assertNotClosed();
      int count = this.resources.getData().read(dst, this.position);
      if (count > 0) {
         this.position += (long)count;
      }

      return count;
   }

   public int write(ByteBuffer src) throws IOException {
      throw new NonWritableChannelException();
   }

   public long position() throws IOException {
      this.assertNotClosed();
      return this.position;
   }

   public SeekableByteChannel position(long position) throws IOException {
      this.assertNotClosed();
      if (position >= 0L && position < this.size) {
         this.position = position;
         return this;
      } else {
         throw new IllegalArgumentException("Position must be in bounds");
      }
   }

   public long size() throws IOException {
      this.assertNotClosed();
      return this.size;
   }

   public SeekableByteChannel truncate(long size) throws IOException {
      throw new NonWritableChannelException();
   }

   private void assertNotClosed() throws ClosedChannelException {
      if (this.closed) {
         throw new ClosedChannelException();
      }
   }

   static class Resources implements Runnable {
      private final ZipContent zipContent;
      private final CloseableDataBlock data;

      Resources(Path path, String nestedEntryName) throws IOException {
         this.zipContent = ZipContent.open(path, nestedEntryName);
         this.data = this.zipContent.openRawZipData();
      }

      DataBlock getData() {
         return this.data;
      }

      public void run() {
         this.releaseAll();
      }

      private void releaseAll() {
         IOException exception = null;

         try {
            this.data.close();
         } catch (IOException var3) {
            exception = var3;
         }

         try {
            this.zipContent.close();
         } catch (IOException var4) {
            if (exception != null) {
               var4.addSuppressed(exception);
            }

            exception = var4;
         }

         if (exception != null) {
            throw new UncheckedIOException(exception);
         }
      }
   }
}
