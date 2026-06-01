package org.springframework.boot.loader.launch;

public class WarLauncher extends ExecutableArchiveLauncher {
   public WarLauncher() throws Exception {
   }

   protected WarLauncher(Archive archive) throws Exception {
      super(archive);
   }

   public boolean isIncludedOnClassPath(Archive.Entry entry) {
      return isLibraryFileOrClassesDirectory(entry);
   }

   protected String getEntryPathPrefix() {
      return "WEB-INF/";
   }

   static boolean isLibraryFileOrClassesDirectory(Archive.Entry entry) {
      String name = entry.name();
      if (entry.isDirectory()) {
         return name.equals("WEB-INF/classes/");
      } else {
         return name.startsWith("WEB-INF/lib/") || name.startsWith("WEB-INF/lib-provided/");
      }
   }

   public static void main(String[] args) throws Exception {
      (new WarLauncher()).launch(args);
   }
}
