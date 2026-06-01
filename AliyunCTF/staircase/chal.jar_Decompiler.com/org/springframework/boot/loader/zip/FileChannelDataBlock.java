package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.channels.ClosedByInterruptException;
import java.nio.channels.ClosedChannelException;
import java.nio.channels.FileChannel;
import java.nio.file.Files;
import java.nio.file.LinkOption;
import java.nio.file.Path;
import java.nio.file.StandardOpenOption;
import java.util.function.Supplier;
import org.springframework.boot.loader.log.DebugLogger;

class FileChannelDataBlock implements CloseableDataBlock {
   private static final DebugLogger debug = DebugLogger.get(FileChannelDataBlock.class);
   static FileChannelDataBlock.Tracker tracker;
   private final FileChannelDataBlock.ManagedFileChannel channel;
   private final long offset;
   private final long size;

   FileChannelDataBlock(Path path) throws IOException {
      this.channel = new FileChannelDataBlock.ManagedFileChannel(path);
      this.offset = 0L;
      this.size = Files.size(path);
   }

   FileChannelDataBlock(FileChannelDataBlock.ManagedFileChannel channel, long offset, long size) {
      this.channel = channel;
      this.offset = offset;
      this.size = size;
   }

   public long size() throws IOException {
      return this.size;
   }

   public int read(ByteBuffer dst, long pos) throws IOException {
      if (pos < 0L) {
         throw new IllegalArgumentException("Position must not be negative");
      } else {
         this.ensureOpen(ClosedChannelException::new);
         int remaining = (int)(this.size - pos);
         if (remaining <= 0) {
            return -1;
         } else {
            int originalDestinationLimit = -1;
            if (dst.remaining() > remaining) {
               originalDestinationLimit = dst.limit();
               dst.limit(dst.position() + remaining);
            }

            int result = this.channel.read(dst, this.offset + pos);
            if (originalDestinationLimit != -1) {
               dst.limit(originalDestinationLimit);
            }

            return result;
         }
      }
   }

   void open() throws IOException {
      this.channel.open();
   }

   public void close() throws IOException {
      this.channel.close();
   }

   <E extends Exception> void ensureOpen(Supplier<E> exceptionSupplier) throws E {
      this.channel.ensureOpen(exceptionSupplier);
   }

   FileChannelDataBlock slice(long offset) throws IOException {
      return this.slice(offset, this.size - offset);
   }

   FileChannelDataBlock slice(long offset, long size) {
      if (offset == 0L && size == this.size) {
         return this;
      } else if (offset < 0L) {
         throw new IllegalArgumentException("Offset must not be negative");
      } else if (size >= 0L && offset + size <= this.size) {
         debug.log("Slicing %s at %s with size %s", this.channel, offset, size);
         return new FileChannelDataBlock(this.channel, this.offset + offset, size);
      } else {
         throw new IllegalArgumentException("Size must not be negative and must be within bounds");
      }
   }

   static class ManagedFileChannel {
      static final int BUFFER_SIZE = 10240;
      private final Path path;
      private int referenceCount;
      private FileChannel fileChannel;
      private ByteBuffer buffer;
      private long bufferPosition = -1L;
      private int bufferSize;
      private final Object lock = new Object();

      ManagedFileChannel(Path path) {
         if (!Files.isRegularFile(path, new LinkOption[0])) {
            throw new IllegalArgumentException(path + " must be a regular file");
         } else {
            this.path = path;
         }
      }

      int read(ByteBuffer dst, long position) throws IOException {
         synchronized(this.lock) {
            if (position < this.bufferPosition || position >= this.bufferPosition + (long)this.bufferSize) {
               this.buffer.clear();

               try {
                  this.bufferSize = this.fileChannel.read(this.buffer, position);
               } catch (ClosedByInterruptException var8) {
                  this.repairFileChannel();
                  throw var8;
               }

               this.bufferPosition = position;
            }

            if (this.bufferSize <= 0) {
               return this.bufferSize;
            } else {
               int offset = (int)(position - this.bufferPosition);
               int length = Math.min(this.bufferSize - offset, dst.remaining());
               dst.put(dst.position(), this.buffer, offset, length);
               dst.position(dst.position() + length);
               return length;
            }
         }
      }

      private void repairFileChannel() throws IOException {
         if (FileChannelDataBlock.tracker != null) {
            FileChannelDataBlock.tracker.closedFileChannel(this.path, this.fileChannel);
         }

         this.fileChannel = FileChannel.open(this.path, StandardOpenOption.READ);
         if (FileChannelDataBlock.tracker != null) {
            FileChannelDataBlock.tracker.openedFileChannel(this.path, this.fileChannel);
         }

      }

      void open() throws IOException {
         synchronized(this.lock) {
            if (this.referenceCount == 0) {
               FileChannelDataBlock.debug.log("Opening '%s'", this.path);
               this.fileChannel = FileChannel.open(this.path, StandardOpenOption.READ);
               this.buffer = ByteBuffer.allocateDirect(10240);
               if (FileChannelDataBlock.tracker != null) {
                  FileChannelDataBlock.tracker.openedFileChannel(this.path, this.fileChannel);
               }
            }

            ++this.referenceCount;
            FileChannelDataBlock.debug.log("Reference count for '%s' incremented to %s", this.path, this.referenceCount);
         }
      }

      void close() throws IOException {
         synchronized(this.lock) {
            if (this.referenceCount != 0) {
               --this.referenceCount;
               if (this.referenceCount == 0) {
                  FileChannelDataBlock.debug.log("Closing '%s'", this.path);
                  this.buffer = null;
                  this.bufferPosition = -1L;
                  this.bufferSize = 0;
                  this.fileChannel.close();
                  if (FileChannelDataBlock.tracker != null) {
                     FileChannelDataBlock.tracker.closedFileChannel(this.path, this.fileChannel);
                  }

                  this.fileChannel = null;
               }

               FileChannelDataBlock.debug.log("Reference count for '%s' decremented to %s", this.path, this.referenceCount);
            }
         }
      }

      <E extends Exception> void ensureOpen(Supplier<E> exceptionSupplier) throws E {
         synchronized(this.lock) {
            if (this.referenceCount == 0 || !this.fileChannel.isOpen()) {
               throw (Exception)exceptionSupplier.get();
            }
         }
      }

      public String toString() {
         return this.path.toString();
      }
   }

   interface Tracker {
      void openedFileChannel(Path path, FileChannel fileChannel);

      void closedFileChannel(Path path, FileChannel fileChannel);
   }
}
