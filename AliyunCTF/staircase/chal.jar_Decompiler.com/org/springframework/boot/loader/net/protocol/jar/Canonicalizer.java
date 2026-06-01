package org.springframework.boot.loader.net.protocol.jar;

final class Canonicalizer {
   private Canonicalizer() {
   }

   static String canonicalizeAfter(String path, int pos) {
      int pathLength = path.length();
      boolean noDotSlash = path.indexOf("./", pos) == -1;
      if (pos < pathLength && (!noDotSlash || path.charAt(pathLength - 1) == '.')) {
         String before = path.substring(0, pos);
         String after = path.substring(pos);
         return before + canonicalize(after);
      } else {
         return path;
      }
   }

   static String canonicalize(String path) {
      path = removeEmbeddedSlashDotDotSlash(path);
      path = removeEmbeddedSlashDotSlash(path);
      path = removeTrailingSlashDotDot(path);
      path = removeTrailingSlashDot(path);
      return path;
   }

   private static String removeEmbeddedSlashDotDotSlash(String path) {
      int index;
      while((index = path.indexOf("/../")) >= 0) {
         int priorSlash = path.lastIndexOf(47, index - 1);
         String after = path.substring(index + 3);
         path = priorSlash >= 0 ? path.substring(0, priorSlash) + after : after;
      }

      return path;
   }

   private static String removeEmbeddedSlashDotSlash(String path) {
      int index;
      while((index = path.indexOf("/./")) >= 0) {
         String before = path.substring(0, index);
         String after = path.substring(index + 2);
         path = before + after;
      }

      return path;
   }

   private static String removeTrailingSlashDot(String path) {
      return !path.endsWith("/.") ? path : path.substring(0, path.length() - 1);
   }

   private static String removeTrailingSlashDotDot(String path) {
      while(path.endsWith("/..")) {
         int index = path.indexOf("/..");
         int priorSlash = path.lastIndexOf(47, index - 1);
         path = priorSlash >= 0 ? path.substring(0, priorSlash + 1) : path.substring(0, index);
      }

      return path;
   }
}
