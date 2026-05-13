package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import org.springframework.boot.loader.log.DebugLogger;

record Zip64EndOfCentralDirectoryRecord(long size, long sizeOfZip64EndOfCentralDirectoryRecord, short versionMadeBy, short versionNeededToExtract, int numberOfThisDisk, int diskWhereCentralDirectoryStarts, long numberOfCentralDirectoryEntriesOnThisDisk, long totalNumberOfCentralDirectoryEntries, long sizeOfCentralDirectory, long offsetToStartOfCentralDirectory) {
   private static final DebugLogger debug = DebugLogger.get(Zip64EndOfCentralDirectoryRecord.class);
   private static final int SIGNATURE = 101075792;
   private static final int MINIMUM_SIZE = 56;

   Zip64EndOfCentralDirectoryRecord(long size, long sizeOfZip64EndOfCentralDirectoryRecord, short versionMadeBy, short versionNeededToExtract, int numberOfThisDisk, int diskWhereCentralDirectoryStarts, long numberOfCentralDirectoryEntriesOnThisDisk, long totalNumberOfCentralDirectoryEntries, long sizeOfCentralDirectory, long offsetToStartOfCentralDirectory) {
      this.size = size;
      this.sizeOfZip64EndOfCentralDirectoryRecord = sizeOfZip64EndOfCentralDirectoryRecord;
      this.versionMadeBy = versionMadeBy;
      this.versionNeededToExtract = versionNeededToExtract;
      this.numberOfThisDisk = numberOfThisDisk;
      this.diskWhereCentralDirectoryStarts = diskWhereCentralDirectoryStarts;
      this.numberOfCentralDirectoryEntriesOnThisDisk = numberOfCentralDirectoryEntriesOnThisDisk;
      this.totalNumberOfCentralDirectoryEntries = totalNumberOfCentralDirectoryEntries;
      this.sizeOfCentralDirectory = sizeOfCentralDirectory;
      this.offsetToStartOfCentralDirectory = offsetToStartOfCentralDirectory;
   }

   static Zip64EndOfCentralDirectoryRecord load(DataBlock dataBlock, Zip64EndOfCentralDirectoryLocator locator) throws IOException {
      if (locator == null) {
         return null;
      } else {
         ByteBuffer buffer = ByteBuffer.allocate(56);
         buffer.order(ByteOrder.LITTLE_ENDIAN);
         long size = locator.pos() - locator.offsetToZip64EndOfCentralDirectoryRecord();
         long pos = locator.pos() - size;
         debug.log("Loading Zip64EndOfCentralDirectoryRecord from position %s size %s", pos, size);
         dataBlock.readFully(buffer, pos);
         buffer.rewind();
         int signature = buffer.getInt();
         if (signature != 101075792) {
            debug.log("Found incorrect Zip64EndOfCentralDirectoryRecord signature %s at position %s", signature, pos);
            throw new IOException("Zip64 'End Of Central Directory Record' not found at position " + pos + ". Zip file is corrupt or includes prefixed bytes which are not supported with Zip64 files");
         } else {
            return new Zip64EndOfCentralDirectoryRecord(size, buffer.getLong(), buffer.getShort(), buffer.getShort(), buffer.getInt(), buffer.getInt(), buffer.getLong(), buffer.getLong(), buffer.getLong(), buffer.getLong());
         }
      }
   }

   public long size() {
      return this.size;
   }

   public long sizeOfZip64EndOfCentralDirectoryRecord() {
      return this.sizeOfZip64EndOfCentralDirectoryRecord;
   }

   public short versionMadeBy() {
      return this.versionMadeBy;
   }

   public short versionNeededToExtract() {
      return this.versionNeededToExtract;
   }

   public int numberOfThisDisk() {
      return this.numberOfThisDisk;
   }

   public int diskWhereCentralDirectoryStarts() {
      return this.diskWhereCentralDirectoryStarts;
   }

   public long numberOfCentralDirectoryEntriesOnThisDisk() {
      return this.numberOfCentralDirectoryEntriesOnThisDisk;
   }

   public long totalNumberOfCentralDirectoryEntries() {
      return this.totalNumberOfCentralDirectoryEntries;
   }

   public long sizeOfCentralDirectory() {
      return this.sizeOfCentralDirectory;
   }

   public long offsetToStartOfCentralDirectory() {
      return this.offsetToStartOfCentralDirectory;
   }
}
