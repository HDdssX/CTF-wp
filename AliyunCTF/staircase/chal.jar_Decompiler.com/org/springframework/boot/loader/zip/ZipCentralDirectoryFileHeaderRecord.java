package org.springframework.boot.loader.zip;

import java.io.IOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.time.ZoneId;
import java.time.ZonedDateTime;
import java.time.temporal.ChronoField;
import java.time.temporal.ChronoUnit;
import java.time.temporal.ValueRange;
import java.util.zip.ZipEntry;
import org.springframework.boot.loader.log.DebugLogger;

record ZipCentralDirectoryFileHeaderRecord(short versionMadeBy, short versionNeededToExtract, short generalPurposeBitFlag, short compressionMethod, short lastModFileTime, short lastModFileDate, int crc32, int compressedSize, int uncompressedSize, short fileNameLength, short extraFieldLength, short fileCommentLength, short diskNumberStart, short internalFileAttributes, int externalFileAttributes, int offsetToLocalHeader) {
   private static final DebugLogger debug = DebugLogger.get(ZipCentralDirectoryFileHeaderRecord.class);
   private static final int SIGNATURE = 33639248;
   private static final int MINIMUM_SIZE = 46;
   static final int FILE_NAME_OFFSET = 46;

   ZipCentralDirectoryFileHeaderRecord(short versionMadeBy, short versionNeededToExtract, short generalPurposeBitFlag, short compressionMethod, short lastModFileTime, short lastModFileDate, int crc32, int compressedSize, int uncompressedSize, short fileNameLength, short extraFieldLength, short fileCommentLength, short diskNumberStart, short internalFileAttributes, int externalFileAttributes, int offsetToLocalHeader) {
      this.versionMadeBy = versionMadeBy;
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
      this.fileCommentLength = fileCommentLength;
      this.diskNumberStart = diskNumberStart;
      this.internalFileAttributes = internalFileAttributes;
      this.externalFileAttributes = externalFileAttributes;
      this.offsetToLocalHeader = offsetToLocalHeader;
   }

   long size() {
      return (long)(46 + this.fileNameLength() + this.extraFieldLength() + this.fileCommentLength());
   }

   void copyTo(DataBlock dataBlock, long pos, ZipEntry zipEntry) throws IOException {
      int fileNameLength = this.fileNameLength() & '\uffff';
      int extraLength = this.extraFieldLength() & '\uffff';
      int commentLength = this.fileCommentLength() & '\uffff';
      zipEntry.setMethod(this.compressionMethod() & '\uffff');
      zipEntry.setTime(this.decodeMsDosFormatDateTime(this.lastModFileDate(), this.lastModFileTime()));
      zipEntry.setCrc((long)this.crc32() & 4294967295L);
      zipEntry.setCompressedSize((long)this.compressedSize() & 4294967295L);
      zipEntry.setSize((long)this.uncompressedSize() & 4294967295L);
      long commentPos;
      if (extraLength > 0) {
         commentPos = pos + 46L + (long)fileNameLength;
         ByteBuffer buffer = ByteBuffer.allocate(extraLength);
         dataBlock.readFully(buffer, commentPos);
         zipEntry.setExtra(buffer.array());
      }

      if ((this.fileCommentLength() & '\uffff') > 0) {
         commentPos = (long)(46 + fileNameLength + extraLength);
         zipEntry.setComment(ZipString.readString(dataBlock, commentPos, (long)commentLength));
      }

   }

   private long decodeMsDosFormatDateTime(short date, short time) {
      int year = getChronoValue((long)((date >> 9 & 127) + 1980), ChronoField.YEAR);
      int month = getChronoValue((long)(date >> 5 & 15), ChronoField.MONTH_OF_YEAR);
      int day = getChronoValue((long)(date & 31), ChronoField.DAY_OF_MONTH);
      int hour = getChronoValue((long)(time >> 11 & 31), ChronoField.HOUR_OF_DAY);
      int minute = getChronoValue((long)(time >> 5 & 63), ChronoField.MINUTE_OF_HOUR);
      int second = getChronoValue((long)(time << 1 & 62), ChronoField.SECOND_OF_MINUTE);
      return ZonedDateTime.of(year, month, day, hour, minute, second, 0, ZoneId.systemDefault()).toInstant().truncatedTo(ChronoUnit.SECONDS).toEpochMilli();
   }

   private static int getChronoValue(long value, ChronoField field) {
      ValueRange range = field.range();
      return Math.toIntExact(Math.min(Math.max(value, range.getMinimum()), range.getMaximum()));
   }

   ZipCentralDirectoryFileHeaderRecord withFileNameLength(short fileNameLength) {
      return this.fileNameLength != fileNameLength ? new ZipCentralDirectoryFileHeaderRecord(this.versionMadeBy, this.versionNeededToExtract, this.generalPurposeBitFlag, this.compressionMethod, this.lastModFileTime, this.lastModFileDate, this.crc32, this.compressedSize, this.uncompressedSize, fileNameLength, this.extraFieldLength, this.fileCommentLength, this.diskNumberStart, this.internalFileAttributes, this.externalFileAttributes, this.offsetToLocalHeader) : this;
   }

   ZipCentralDirectoryFileHeaderRecord withOffsetToLocalHeader(int offsetToLocalHeader) {
      return this.offsetToLocalHeader != offsetToLocalHeader ? new ZipCentralDirectoryFileHeaderRecord(this.versionMadeBy, this.versionNeededToExtract, this.generalPurposeBitFlag, this.compressionMethod, this.lastModFileTime, this.lastModFileDate, this.crc32, this.compressedSize, this.uncompressedSize, this.fileNameLength, this.extraFieldLength, this.fileCommentLength, this.diskNumberStart, this.internalFileAttributes, this.externalFileAttributes, offsetToLocalHeader) : this;
   }

   byte[] asByteArray() {
      ByteBuffer buffer = ByteBuffer.allocate(46);
      buffer.order(ByteOrder.LITTLE_ENDIAN);
      buffer.putInt(33639248);
      buffer.putShort(this.versionMadeBy);
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
      buffer.putShort(this.fileCommentLength);
      buffer.putShort(this.diskNumberStart);
      buffer.putShort(this.internalFileAttributes);
      buffer.putInt(this.externalFileAttributes);
      buffer.putInt(this.offsetToLocalHeader);
      return buffer.array();
   }

   static ZipCentralDirectoryFileHeaderRecord load(DataBlock dataBlock, long pos) throws IOException {
      debug.log("Loading CentralDirectoryFileHeaderRecord from position %s", pos);
      ByteBuffer buffer = ByteBuffer.allocate(46);
      buffer.order(ByteOrder.LITTLE_ENDIAN);
      dataBlock.readFully(buffer, pos);
      buffer.rewind();
      int signature = buffer.getInt();
      if (signature != 33639248) {
         debug.log("Found incorrect CentralDirectoryFileHeaderRecord signature %s at position %s", signature, pos);
         throw new IOException("Zip 'Central Directory File Header Record' not found at position " + pos);
      } else {
         return new ZipCentralDirectoryFileHeaderRecord(buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getInt(), buffer.getInt(), buffer.getInt(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getShort(), buffer.getInt(), buffer.getInt());
      }
   }

   public short versionMadeBy() {
      return this.versionMadeBy;
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

   public short fileCommentLength() {
      return this.fileCommentLength;
   }

   public short diskNumberStart() {
      return this.diskNumberStart;
   }

   public short internalFileAttributes() {
      return this.internalFileAttributes;
   }

   public int externalFileAttributes() {
      return this.externalFileAttributes;
   }

   public int offsetToLocalHeader() {
      return this.offsetToLocalHeader;
   }
}
