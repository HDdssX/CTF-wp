package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import org.springframework.boot.loader.log.DebugLogger;

record ZipLocalFileHeaderRecord(short versionNeededToExtract, short generalPurposeBitFlag, short compressionMethod, short lastModFileTime, short lastModFileDate, int crc32, int compressedSize, int uncompressedSize, short fileNameLength, short extraFieldLength) {
   private static final DebugLogger debug = DebugLogger.get(ZipLocalFileHeaderRecord.class);
   private static final int SIGNATURE = 67324752;
   private static final int MINIMUM_SIZE = 30;

   ZipLocalFileHeaderRecord(short versionNeededToExtract, short generalPurposeBitFlag, short compressionMethod, short lastModFileTime, short lastModFileDate, int crc32, int compressedSize, int uncompressedSize, short fileNameLength, short extraFieldLength) {
      this.versionNeededToExtract = versionNeededToExtract;
      this.generalPurposeBitFlag = generalPurposeBitFlag;
      this.compressionMethod = compressionMethod;
      this.lastModFileTime = lastModFileTime;
      this.lastModFileDate = lastModFileDate;
      this.crc32 = crc32;
      this.compressedSize = compressedSize;
      this.uncompressedSize = uncompressedSize;
      this.fileNameLength = fileNameLength;
      this.extraFieldLength = extraFieldLength;
   }

   long size() {
      return (long)(30 + this.fileNameLength() + this.extraFieldLength());
   }

   ZipLocalFileHeaderRecord withExtraFieldLength(short extraFieldLength) {
      return new ZipLocalFileHeaderRecord(this.versionNeededToExtract, this.generalPurposeBitFlag, this.compressionMethod, this.lastModFileTime, this.lastModFileDate, this.crc32, this.compressedSize, this.uncompressedSize, this.fileNameLength, extraFieldLength);
   }

   ZipLocalFileHeaderRecord withFileNameLength(short fileNameLength) {
      return new ZipLocalFileHeaderRecord(this.versionNeededToExtract, this.generalPurposeBitFlag, this.compressionMethod, this.lastModFileTime, this.lastModFileDate, this.crc32, this.compressedSize, this.uncompressedSize, fileNameLength, this.extraFieldLength);
   }

   byte[] asByteArray() {
      ByteBuffer buffer = ByteBuffer.allocate(30);
      buffer.order(ByteOrder.LITTLE_ENDIAN);
      buffer.putInt(67324752);
      buffer.putShort(this.versionNeededToExtract);
      buffer.putShort(this.generalPurposeBitFlag);
      buffer.putShort(this.compressionMethod);
      buffer.putShort(this.lastModFileTime);
      buffer.putShort(this.lastModFileDate);
      buffer.putInt(this.crc32);
      buffer.putInt(this.compressedSize);
      buffer.putInt(this.uncompressedSize);
      buffer.putShort(this.fileNameLength);
      buffer.putShort(this.extraFieldLength);
      return buffer.array();
   }

   static ZipLocalFileHeaderRecord load(DataBlock dataBlock, long pos) throws IOException {
      debug.log("Loading LocalFileHeaderRecord from position %s", pos);
      ByteBuffer buffer = ByteBuffer.allocate(30);
      buffer.order(ByteOrder.LITTLE_ENDIAN);
      dataBlock.readFully(buffer, pos);
      buffer.rewind();
      if (buffer.getInt() != 67324752) {
         throw new IOException("Zip 'Local File Header Record' not found at position " + pos);
      } else {
         return new ZipLocalFileHeaderRecord(buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getInt(), buffer.getInt(), buffer.getInt(), buffer.getShort(), buffer.getShort());
      }
   }

   public short versionNeededToExtract() {
      return this.versionNeededToExtract;
   }

   public short generalPurposeBitFlag() {
      return this.generalPurposeBitFlag;
   }

   public short compressionMethod() {
      return this.compressionMethod;
   }

   public short lastModFileTime() {
      return this.lastModFileTime;
   }

   public short lastModFileDate() {
      return this.lastModFileDate;
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

   public short fileNameLength() {
      return this.fileNameLength;
   }

   public short extraFieldLength() {
      return this.extraFieldLength;
   }
}
