package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import org.springframework.boot.loader.log.DebugLogger;

record ZipDataDescriptorRecord(boolean includeSignature, int crc32, int compressedSize, int uncompressedSize) {
   private static final DebugLogger debug = DebugLogger.get(ZipDataDescriptorRecord.class);
   private static final int SIGNATURE = 134695760;
   private static final int DATA_SIZE = 12;
   private static final int SIGNATURE_SIZE = 4;

   ZipDataDescriptorRecord(boolean includeSignature, int crc32, int compressedSize, int uncompressedSize) {
      this.includeSignature = includeSignature;
      this.crc32 = crc32;
      this.compressedSize = compressedSize;
      this.uncompressedSize = uncompressedSize;
   }

   long size() {
      return !this.includeSignature() ? 12L : 16L;
   }

   byte[] asByteArray() {
      ByteBuffer buffer = ByteBuffer.allocate((int)this.size());
      buffer.order(ByteOrder.LITTLE_ENDIAN);
      if (this.includeSignature) {
         buffer.putInt(134695760);
      }

      buffer.putInt(this.crc32);
      buffer.putInt(this.compressedSize);
      buffer.putInt(this.uncompressedSize);
      return buffer.array();
   }

   static ZipDataDescriptorRecord load(DataBlock dataBlock, long pos) throws IOException {
      debug.log("Loading ZipDataDescriptorRecord from position %s", pos);
      ByteBuffer buffer = ByteBuffer.allocate(16);
      buffer.order(ByteOrder.LITTLE_ENDIAN);
      buffer.limit(4);
      dataBlock.readFully(buffer, pos);
      buffer.rewind();
      int signatureOrCrc = buffer.getInt();
      boolean hasSignature = signatureOrCrc == 134695760;
      buffer.rewind();
      buffer.limit(!hasSignature ? 8 : 12);
      dataBlock.readFully(buffer, pos + 4L);
      buffer.rewind();
      return new ZipDataDescriptorRecord(hasSignature, !hasSignature ? signatureOrCrc : buffer.getInt(), buffer.getInt(), buffer.getInt());
   }

   static boolean isPresentBasedOnFlag(ZipLocalFileHeaderRecord localRecord) {
      return isPresentBasedOnFlag(localRecord.generalPurposeBitFlag());
   }

   static boolean isPresentBasedOnFlag(ZipCentralDirectoryFileHeaderRecord centralRecord) {
      return isPresentBasedOnFlag(centralRecord.generalPurposeBitFlag());
   }

   static boolean isPresentBasedOnFlag(int generalPurposeBitFlag) {
      return (generalPurposeBitFlag & 8) != 0;
   }

   public boolean includeSignature() {
      return this.includeSignature;
   }

   public int crc32() {
      return this.crc32;
   }

   public int compressedSize() {
      return this.compressedSize;
   }

   public int uncompressedSize() {
      return this.uncompressedSize;
   }
}
