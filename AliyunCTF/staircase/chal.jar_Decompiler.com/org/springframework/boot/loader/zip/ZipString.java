package org.springframework.boot.loader.zip;

import java.io.EOFException;
import java.io.IOException;
import java.io.UncheckedIOException;
import java.nio.ByteBuffer;
import java.nio.ByteOrder;
import java.nio.charset.StandardCharsets;
import org.springframework.boot.loader.log.DebugLogger;

final class ZipString {
   private static final DebugLogger debug = DebugLogger.get(ZipString.class);
   static final int BUFFER_SIZE = 256;
   private static final int[] INITIAL_BYTE_BITMASK = new int[]{127, 31, 15, 7};
   private static final int SUBSEQUENT_BYTE_BITMASK = 63;
   private static final int EMPTY_HASH = "".hashCode();
   private static final int EMPTY_SLASH_HASH = "/".hashCode();

   private ZipString() {
   }

   static int hash(CharSequence charSequence, boolean addEndSlash) {
      return hash(0, charSequence, addEndSlash);
   }

   static int hash(int initialHash, CharSequence charSequence, boolean addEndSlash) {
      if (charSequence != null && !charSequence.isEmpty()) {
         boolean endsWithSlash = charSequence.charAt(charSequence.length() - 1) == '/';
         int hash = initialHash;
         if (charSequence instanceof String && initialHash == 0) {
            hash = charSequence.hashCode();
         } else {
            for(int i = 0; i < charSequence.length(); ++i) {
               char ch = charSequence.charAt(i);
               hash = 31 * hash + ch;
            }
         }

         hash = addEndSlash && !endsWithSlash ? 31 * hash + 47 : hash;
         debug.log("%s calculated for charsequence '%s' (addEndSlash=%s)", hash, charSequence, endsWithSlash);
         return hash;
      } else {
         return !addEndSlash ? EMPTY_HASH : EMPTY_SLASH_HASH;
      }
   }

   static int hash(ByteBuffer buffer, DataBlock dataBlock, long pos, int len, boolean addEndSlash) throws IOException {
      if (len == 0) {
         return !addEndSlash ? EMPTY_HASH : EMPTY_SLASH_HASH;
      } else {
         buffer = buffer != null ? buffer : ByteBuffer.allocate(256);
         byte[] bytes = buffer.array();
         int hash = 0;
         char lastChar = 0;

         while(true) {
            while(len > 0) {
               int count = readInBuffer(dataBlock, pos, buffer, len);
               len -= count;
               pos += (long)count;
               int byteIndex = 0;

               while(byteIndex < count) {
                  int codePointSize = getCodePointSize(bytes, byteIndex);
                  if (!hasEnoughBytes(byteIndex, codePointSize, count)) {
                     --pos;
                     ++len;
                     break;
                  }

                  int codePoint = getCodePoint(bytes, byteIndex, codePointSize);
                  byteIndex += codePointSize;
                  if (codePoint <= 65535) {
                     lastChar = (char)(codePoint & '\uffff');
                     hash = 31 * hash + lastChar;
                  } else {
                     lastChar = 0;
                     hash = 31 * hash + Character.highSurrogate(codePoint);
                     hash = 31 * hash + Character.lowSurrogate(codePoint);
                  }
               }
            }

            hash = addEndSlash && lastChar != '/' ? 31 * hash + 47 : hash;
            debug.log("%08X calculated for datablock position %s size %s (addEndSlash=%s)", hash, pos, len, addEndSlash);
            return hash;
         }
      }
   }

   static boolean matches(ByteBuffer buffer, DataBlock dataBlock, long pos, int len, CharSequence charSequence, boolean addSlash) {
      if (charSequence.isEmpty()) {
         return true;
      } else {
         buffer = buffer != null ? buffer : ByteBuffer.allocate(256);

         try {
            return compare(buffer, dataBlock, pos, len, charSequence, !addSlash ? ZipString.CompareType.MATCHES : ZipString.CompareType.MATCHES_ADDING_SLASH) != -1;
         } catch (IOException var8) {
            throw new UncheckedIOException(var8);
         }
      }
   }

   static int startsWith(ByteBuffer buffer, DataBlock dataBlock, long pos, int len, CharSequence charSequence) {
      if (charSequence.isEmpty()) {
         return 0;
      } else {
         buffer = buffer != null ? buffer : ByteBuffer.allocate(256);

         try {
            return compare(buffer, dataBlock, pos, len, charSequence, ZipString.CompareType.STARTS_WITH);
         } catch (IOException var7) {
            throw new UncheckedIOException(var7);
         }
      }
   }

   private static int compare(ByteBuffer buffer, DataBlock dataBlock, long pos, int len, CharSequence charSequence, ZipString.CompareType compareType) throws IOException {
      if (charSequence.isEmpty()) {
         return 0;
      } else {
         boolean addSlash = compareType == ZipString.CompareType.MATCHES_ADDING_SLASH && !endsWith(charSequence, '/');
         int charSequenceIndex = 0;
         int maxCharSequenceLength = !addSlash ? charSequence.length() : charSequence.length() + 1;
         int result = 0;
         byte[] bytes = buffer.array();

         while(len > 0) {
            int count = readInBuffer(dataBlock, pos, buffer, len);
            len -= count;
            pos += (long)count;

            int codePointSize;
            for(int byteIndex = 0; byteIndex < count; byteIndex += codePointSize) {
               codePointSize = getCodePointSize(bytes, byteIndex);
               if (!hasEnoughBytes(byteIndex, codePointSize, count)) {
                  --pos;
                  ++len;
                  break;
               }

               int codePoint = getCodePoint(bytes, byteIndex, codePointSize);
               result += codePointSize;
               char ch;
               if (codePoint <= 65535) {
                  ch = (char)(codePoint & '\uffff');
                  if (charSequenceIndex >= maxCharSequenceLength || getChar(charSequence, charSequenceIndex++) != ch) {
                     return -1;
                  }
               } else {
                  ch = Character.highSurrogate(codePoint);
                  if (charSequenceIndex >= maxCharSequenceLength || getChar(charSequence, charSequenceIndex++) != ch) {
                     return -1;
                  }

                  ch = Character.lowSurrogate(codePoint);
                  if (charSequenceIndex >= charSequence.length() || getChar(charSequence, charSequenceIndex++) != ch) {
                     return -1;
                  }
               }

               if (compareType == ZipString.CompareType.STARTS_WITH && charSequenceIndex >= charSequence.length()) {
                  return result;
               }
            }
         }

         return charSequenceIndex >= charSequence.length() ? result : -1;
      }
   }

   private static boolean hasEnoughBytes(int byteIndex, int codePointSize, int count) {
      return byteIndex + codePointSize - 1 < count;
   }

   private static boolean endsWith(CharSequence charSequence, char ch) {
      return !charSequence.isEmpty() && charSequence.charAt(charSequence.length() - 1) == ch;
   }

   private static char getChar(CharSequence charSequence, int index) {
      return index != charSequence.length() ? charSequence.charAt(index) : '/';
   }

   static String readString(DataBlock data, long pos, long len) {
      try {
         if (len > 2147483647L) {
            throw new IllegalStateException("String is too long to read");
         } else {
            ByteBuffer buffer = ByteBuffer.allocate((int)len);
            buffer.order(ByteOrder.LITTLE_ENDIAN);
            data.readFully(buffer, pos);
            return new String(buffer.array(), StandardCharsets.UTF_8);
         }
      } catch (IOException var6) {
         throw new UncheckedIOException(var6);
      }
   }

   private static int readInBuffer(DataBlock dataBlock, long pos, ByteBuffer buffer, int maxLen) throws IOException {
      buffer.clear();
      if (buffer.remaining() > maxLen) {
         buffer.limit(maxLen);
      }

      int count = dataBlock.read(buffer, pos);
      if (count <= 0) {
         throw new EOFException();
      } else {
         return count;
      }
   }

   private static int getCodePointSize(byte[] bytes, int i) {
      int b = bytes[i] & 255;
      if ((b & 128) == 0) {
         return 1;
      } else if ((b & 224) == 192) {
         return 2;
      } else {
         return (b & 240) == 224 ? 3 : 4;
      }
   }

   private static int getCodePoint(byte[] bytes, int i, int codePointSize) {
      int codePoint = bytes[i] & 255;
      codePoint &= INITIAL_BYTE_BITMASK[codePointSize - 1];

      for(int j = 1; j < codePointSize; ++j) {
         codePoint = (codePoint << 6) + (bytes[i + j] & 63);
      }

      return codePoint;
   }

   private static enum CompareType {
      MATCHES,
      MATCHES_ADDING_SLASH,
      STARTS_WITH;

      // $FF: synthetic method
      private static ZipString.CompareType[] $values() {
         return new ZipString.CompareType[]{MATCHES, MATCHES_ADDING_SLASH, STARTS_WITH};
      }
   }
}
