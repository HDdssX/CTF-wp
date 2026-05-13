package org.springframework.boot.loader.launch;

public class JarLauncher extends ExecutableArchiveLauncher {
   public JarLauncher() throws Exception {
   }

   protected JarLauncher(Archive archive) throws Exception {
      super(archive);
   }

   protected boolean isIncludedOnClassPath(Archive.Entry entry) {
      return isLibraryFileOrClassesDirectory(entry);
   }

   protected String getEntryPathPrefix() {
      return "BOOT-INF/";
   }

   static boolean isLibraryFileOrClassesDirectory(Archive.Entry entry) {
      String name = entry.name();
      return entry.isDirectory() ? name.equals("BOOT-INF/classes/") : name.startsWith("BOOT-INF/lib/");
   }

   public static void main(String[] args) throws Exception {
      (new JarLauncher()).launch(args);
   }
}
