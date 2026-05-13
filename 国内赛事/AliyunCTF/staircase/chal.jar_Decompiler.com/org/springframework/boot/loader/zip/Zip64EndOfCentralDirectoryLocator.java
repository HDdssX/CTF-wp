package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import org.springframework.boot.loader.log.DebugLogger;

record Zip64EndOfCentralDirectoryLocator(long pos, int numberOfThisDisk, long offsetToZip64EndOfCentralDirectoryRecord, int totalNumberOfDisks) {
   private static final DebugLogger debug = DebugLogger.get(Zip64EndOfCentralDirectoryLocator.class);
   private static final int SIGNATURE = 117853008;
   static final int SIZE = 20;

   Zip64EndOfCentralDirectoryLocator(long pos, int numberOfThisDisk, long offsetToZip64EndOfCentralDirectoryRecord, int totalNumberOfDisks) {
      this.pos = pos;
      this.numberOfThisDisk = numberOfThisDisk;
      this.offsetToZip64EndOfCentralDirectoryRecord = offsetToZip64EndOfCentralDirectoryRecord;
      this.totalNumberOfDisks = totalNumberOfDisks;
   }

   static Zip64EndOfCentralDirectoryLocator find(DataBlock dataBlock, long endOfCentralDirectoryPos) throws IOException {
      debug.log("Finding Zip64EndOfCentralDirectoryLocator from EOCD at %s", endOfCentralDirectoryPos);
      long pos = endOfCentralDirectoryPos - 20L;
      if (pos < 0L) {
         debug.log("No Zip64EndOfCentralDirectoryLocator due to negative position %s", pos);
         return null;
      } else {
         ByteBuffer buffer = ByteBuffer.allocate(20);
         buffer.order(ByteOrder.LITTLE_ENDIAN);
         dataBlock.read(buffer, pos);
         buffer.rewind();
         int signature = buffer.getInt();
         if (signature != 117853008) {
            debug.log("Found incorrect Zip64EndOfCentralDirectoryLocator signature %s at position %s", signature, pos);
            return null;
         } else {
            debug.log("Found Zip64EndOfCentralDirectoryLocator at position %s", pos);
            return new Zip64EndOfCentralDirectoryLocator(pos, buffer.getInt(), buffer.getLong(), buffer.getInt());
         }
      }
   }

   public long pos() {
      return this.pos;
   }

   public int numberOfThisDisk() {
      return this.numberOfThisDisk;
   }

   public long offsetToZip64EndOfCentralDirectoryRecord() {
      return this.offsetToZip64EndOfCentralDirectoryRecord;
   }

   public int totalNumberOfDisks() {
      return this.totalNumberOfDisks;
   }
}
