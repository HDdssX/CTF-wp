package org.springframework.boot.loader.launch;

import java.io.File;
import java.io.FileInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.lang.reflect.Constructor;
import java.net.HttpURLConnection;
import java.net.URL;
import java.net.URLConnection;
import java.net.URLDecoder;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Collection;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashSet;
import java.util.List;
import java.util.Locale;
import java.util.Properties;
import java.util.Set;
import java.util.function.Predicate;
import java.util.jar.Manifest;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import org.springframework.boot.loader.log.DebugLogger;
import org.springframework.boot.loader.net.protocol.jar.JarUrl;

public class PropertiesLauncher extends Launcher {
   public static final String MAIN = "loader.main";
   public static final String PATH = "loader.path";
   public static final String HOME = "loader.home";
   public static final String ARGS = "loader.args";
   public static final String CONFIG_NAME = "loader.config.name";
   public static final String CONFIG_LOCATION = "loader.config.location";
   public static final String SET_SYSTEM_PROPERTIES = "loader.system";
   private static final URL[] NO_URLS = new URL[0];
   private static final Pattern WORD_SEPARATOR = Pattern.compile("\\W+");
   private static final String NESTED_ARCHIVE_SEPARATOR;
   private static final String JAR_FILE_PREFIX = "jar:file:";
   private static final DebugLogger debug;
   private final Archive archive;
   private final File homeDirectory;
   private final List<String> paths;
   private final Properties properties;

   public PropertiesLauncher() throws Exception {
      this(Archive.create(Launcher.class));
   }

   PropertiesLauncher(Archive archive) throws Exception {
      this.properties = new Properties();
      this.archive = archive;
      this.homeDirectory = this.getHomeDirectory();
      this.initializeProperties();
      this.paths = this.getPaths();
   }

   protected File getHomeDirectory() throws Exception {
      return new File(this.getPropertyWithDefault("loader.home", "${user.dir}"));
   }

   private void initializeProperties() throws Exception {
      List<String> configs = new ArrayList();
      if (this.getProperty("loader.config.location") != null) {
         configs.add(this.getProperty("loader.config.location"));
      } else {
         String[] names = this.getPropertyWithDefault("loader.config.name", "loader").split(",");
         String[] var3 = names;
         int var4 = names.length;

         for(int var5 = 0; var5 < var4; ++var5) {
            String name = var3[var5];
            String propertiesFile = name + ".properties";
            configs.add("file:" + this.homeDirectory + "/" + propertiesFile);
            configs.add("classpath:" + propertiesFile);
            configs.add("classpath:BOOT-INF/classes/" + propertiesFile);
         }
      }

      Iterator var10 = configs.iterator();

      while(true) {
         if (var10.hasNext()) {
            String config = (String)var10.next();
            InputStream resource = this.getResource(config);

            label45: {
               try {
                  if (resource != null) {
                     debug.log("Found: %s", config);
                     this.loadResource(resource);
                     break label45;
                  }

                  debug.log("Not found: %s", config);
               } catch (Throwable var9) {
                  if (resource != null) {
                     try {
                        resource.close();
                     } catch (Throwable var8) {
                        var9.addSuppressed(var8);
                     }
                  }

                  throw var9;
               }

               if (resource != null) {
                  resource.close();
               }
               continue;
            }

            if (resource != null) {
               resource.close();
            }

            return;
         }

         return;
      }
   }

   private InputStream getResource(String config) throws Exception {
      if (config.startsWith("classpath:")) {
         return this.getClasspathResource(config.substring("classpath:".length()));
      } else {
         config = this.handleUrl(config);
         return this.isUrl(config) ? this.getURLResource(config) : this.getFileResource(config);
      }
   }

   private InputStream getClasspathResource(String config) {
      config = this.stripLeadingSlashes(config);
      config = "/" + config;
      debug.log("Trying classpath: %s", config);
      return this.getClass().getResourceAsStream(config);
   }

   private String handleUrl(String path) {
      if (path.startsWith("jar:file:") || path.startsWith("file:")) {
         path = URLDecoder.decode(path, StandardCharsets.UTF_8);
         if (path.startsWith("file:")) {
            path = path.substring("file:".length());
            if (path.startsWith("//")) {
               path = path.substring(2);
            }
         }
      }

      return path;
   }

   private boolean isUrl(String config) {
      return config.contains("://");
   }

   private InputStream getURLResource(String config) throws Exception {
      URL url = new URL(config);
      if (this.exists(url)) {
         URLConnection connection = url.openConnection();

         try {
            return connection.getInputStream();
         } catch (IOException var5) {
            this.disconnect(connection);
            throw var5;
         }
      } else {
         return null;
      }
   }

   private boolean exists(URL url) throws IOException {
      URLConnection connection = url.openConnection();

      boolean var9;
      try {
         connection.setUseCaches(connection.getClass().getSimpleName().startsWith("JNLP"));
         if (connection instanceof HttpURLConnection) {
            HttpURLConnection httpConnection = (HttpURLConnection)connection;
            httpConnection.setRequestMethod("HEAD");
            int responseCode = httpConnection.getResponseCode();
            boolean var5;
            if (responseCode == 200) {
               var5 = true;
               return var5;
            }

            if (responseCode == 404) {
               var5 = false;
               return var5;
            }
         }

         var9 = connection.getContentLength() >= 0;
      } finally {
         this.disconnect(connection);
      }

      return var9;
   }

   private void disconnect(URLConnection connection) {
      if (connection instanceof HttpURLConnection) {
         HttpURLConnection httpConnection = (HttpURLConnection)connection;
         httpConnection.disconnect();
      }

   }

   private InputStream getFileResource(String config) throws Exception {
      File file = new File(config);
      debug.log("Trying file: %s", config);
      return !file.canRead() ? null : new FileInputStream(file);
   }

   private void loadResource(InputStream resource) throws Exception {
      this.properties.load(resource);
      this.resolvePropertyPlaceholders();
      if ("true".equalsIgnoreCase(this.getProperty("loader.system"))) {
         this.addToSystemProperties();
      }

   }

   private void resolvePropertyPlaceholders() {
      Iterator var1 = this.properties.stringPropertyNames().iterator();

      while(var1.hasNext()) {
         String name = (String)var1.next();
         String value = this.properties.getProperty(name);
         String resolved = SystemPropertyUtils.resolvePlaceholders(this.properties, value);
         if (resolved != null) {
            this.properties.put(name, resolved);
         }
      }

   }

   private void addToSystemProperties() {
      debug.log("Adding resolved properties to System properties");
      Iterator var1 = this.properties.stringPropertyNames().iterator();

      while(var1.hasNext()) {
         String name = (String)var1.next();
         String value = this.properties.getProperty(name);
         System.setProperty(name, value);
      }

   }

   private List<String> getPaths() throws Exception {
      String path = this.getProperty("loader.path");
      List<String> paths = path != null ? this.parsePathsProperty(path) : Collections.emptyList();
      debug.log("Nested archive paths: %s", this.paths);
      return paths;
   }

   private List<String> parsePathsProperty(String commaSeparatedPaths) {
      List<String> paths = new ArrayList();
      String[] var3 = commaSeparatedPaths.split(",");
      int var4 = var3.length;

      for(int var5 = 0; var5 < var4; ++var5) {
         String path = var3[var5];
         path = this.cleanupPath(path);
         path = path.isEmpty() ? "/" : path;
         paths.add(path);
      }

      if (paths.isEmpty()) {
         paths.add("lib");
      }

      return paths;
   }

   private String cleanupPath(String path) {
      path = path.trim();
      if (path.startsWith("./")) {
         path = path.substring(2);
      }

      if (this.isArchive(path)) {
         return path;
      } else if (path.endsWith("/*")) {
         return path.substring(0, path.length() - 1);
      } else {
         return !path.endsWith("/") && !path.equals(".") ? path + "/" : path;
      }
   }

   protected ClassLoader createClassLoader(Collection<URL> urls) throws Exception {
      String loaderClassName = this.getProperty("loader.classLoader");
      if (loaderClassName == null) {
         return super.createClassLoader(urls);
      } else {
         ClassLoader parent = this.getClass().getClassLoader();
         ClassLoader classLoader = new LaunchedClassLoader(false, (URL[])urls.toArray(new URL[0]), parent);
         debug.log("Classpath for custom loader: %s", urls);
         ClassLoader classLoader = this.wrapWithCustomClassLoader(classLoader, loaderClassName);
         debug.log("Using custom class loader: %s", loaderClassName);
         return classLoader;
      }
   }

   private ClassLoader wrapWithCustomClassLoader(ClassLoader parent, String loaderClassName) throws Exception {
      PropertiesLauncher.Instantiator<ClassLoader> instantiator = new PropertiesLauncher.Instantiator(parent, loaderClassName);
      ClassLoader loader = (ClassLoader)instantiator.declaredConstructor(ClassLoader.class).newInstance(parent);
      loader = loader != null ? loader : (ClassLoader)instantiator.declaredConstructor(URL[].class, ClassLoader.class).newInstance(NO_URLS, parent);
      loader = loader != null ? loader : (ClassLoader)instantiator.constructWithoutParameters();
      if (loader != null) {
         return loader;
      } else {
         throw new IllegalStateException("Unable to create class loader for " + loaderClassName);
      }
   }

   protected Archive getArchive() {
      return null;
   }

   protected String getMainClass() throws Exception {
      String mainClass = this.getProperty("loader.main", "Start-Class");
      if (mainClass == null) {
         throw new IllegalStateException("No '%s' or 'Start-Class' specified".formatted(new Object[]{"loader.main"}));
      } else {
         return mainClass;
      }
   }

   protected String[] getArgs(String... args) throws Exception {
      String loaderArgs = this.getProperty("loader.args");
      return loaderArgs != null ? this.merge(loaderArgs.split("\\s+"), args) : args;
   }

   private String[] merge(String[] a1, String[] a2) {
      String[] result = new String[a1.length + a2.length];
      System.arraycopy(a1, 0, result, 0, a1.length);
      System.arraycopy(a2, 0, result, a1.length, a2.length);
      return result;
   }

   private String getProperty(String name) throws Exception {
      return this.getProperty(name, (String)null, (String)null);
   }

   private String getProperty(String name, String manifestKey) throws Exception {
      return this.getProperty(name, manifestKey, (String)null);
   }

   private String getPropertyWithDefault(String name, String defaultValue) throws Exception {
      return this.getProperty(name, (String)null, defaultValue);
   }

   private String getProperty(String name, String manifestKey, String defaultValue) throws Exception {
      manifestKey = manifestKey != null ? manifestKey : toCamelCase(name.replace('.', '-'));
      String value = SystemPropertyUtils.getProperty(name);
      if (value != null) {
         return this.getResolvedProperty(name, manifestKey, value, "environment");
      } else if (this.properties.containsKey(name)) {
         value = this.properties.getProperty(name);
         return this.getResolvedProperty(name, manifestKey, value, "properties");
      } else {
         if (this.homeDirectory != null) {
            try {
               label60: {
                  ExplodedArchive explodedArchive = new ExplodedArchive(this.homeDirectory);

                  String var6;
                  label49: {
                     try {
                        value = this.getManifestValue(explodedArchive, manifestKey);
                        if (value != null) {
                           var6 = this.getResolvedProperty(name, manifestKey, value, "home directory manifest");
                           break label49;
                        }
                     } catch (Throwable var9) {
                        try {
                           explodedArchive.close();
                        } catch (Throwable var8) {
                           var9.addSuppressed(var8);
                        }

                        throw var9;
                     }

                     explodedArchive.close();
                     break label60;
                  }

                  explodedArchive.close();
                  return var6;
               }
            } catch (IllegalStateException var10) {
            }
         }

         value = this.getManifestValue(this.archive, manifestKey);
         return value != null ? this.getResolvedProperty(name, manifestKey, value, "manifest") : SystemPropertyUtils.resolvePlaceholders(this.properties, defaultValue);
      }
   }

   String getManifestValue(Archive archive, String manifestKey) throws Exception {
      Manifest manifest = archive.getManifest();
      return manifest != null ? manifest.getMainAttributes().getValue(manifestKey) : null;
   }

   private String getResolvedProperty(String name, String manifestKey, String value, String from) {
      value = SystemPropertyUtils.resolvePlaceholders(this.properties, value);
      String altName = manifestKey != null && !manifestKey.equals(name) ? "[%s] ".formatted(new Object[]{manifestKey}) : "";
      debug.log("Property '%s'%s from %s: %s", name, altName, from, value);
      return value;
   }

   void close() throws Exception {
      if (this.archive != null) {
         this.archive.close();
      }

   }

   public static String toCamelCase(CharSequence string) {
      if (string == null) {
         return null;
      } else {
         StringBuilder result = new StringBuilder();
         Matcher matcher = WORD_SEPARATOR.matcher(string);

         int pos;
         for(pos = 0; matcher.find(); pos = matcher.end()) {
            result.append(capitalize(string.subSequence(pos, matcher.end()).toString()));
         }

         result.append(capitalize(string.subSequence(pos, string.length()).toString()));
         return result.toString();
      }
   }

   private static String capitalize(String str) {
      char var10000 = Character.toUpperCase(str.charAt(0));
      return var10000 + str.substring(1);
   }

   protected Set<URL> getClassPathUrls() throws Exception {
      Set<URL> urls = new LinkedHashSet();
      Iterator var2 = this.getPaths().iterator();

      while(var2.hasNext()) {
         String path = (String)var2.next();
         path = this.cleanupPath(this.handleUrl(path));
         urls.addAll(this.getClassPathUrlsForPath(path));
      }

      urls.addAll(this.getClassPathUrlsForRoot());
      debug.log("Using class path URLs %s", urls);
      return urls;
   }

   private Set<URL> getClassPathUrlsForPath(String path) throws Exception {
      File file = !this.isAbsolutePath(path) ? new File(this.homeDirectory, path) : new File(path);
      Set<URL> urls = new LinkedHashSet();
      if (!"/".equals(path) && file.isDirectory()) {
         ExplodedArchive explodedArchive = new ExplodedArchive(file);

         try {
            debug.log("Adding classpath entries from directory %s", file);
            urls.add(file.toURI().toURL());
            urls.addAll(explodedArchive.getClassPathUrls(this::isArchive));
         } catch (Throwable var8) {
            try {
               explodedArchive.close();
            } catch (Throwable var7) {
               var8.addSuppressed(var7);
            }

            throw var8;
         }

         explodedArchive.close();
      }

      if (!file.getPath().contains(NESTED_ARCHIVE_SEPARATOR) && this.isArchive(file.getName())) {
         debug.log("Adding classpath entries from jar/zip archive %s", path);
         urls.add(file.toURI().toURL());
      }

      Set<URL> nested = this.getClassPathUrlsForNested(path);
      if (!nested.isEmpty()) {
         debug.log("Adding classpath entries from nested %s", path);
         urls.addAll(nested);
      }

      return urls;
   }

   private Set<URL> getClassPathUrlsForNested(String path) throws Exception {
      boolean isJustArchive = this.isArchive(path);
      if ((path.equals("/") || !path.startsWith("/")) && (!this.archive.isExploded() || !this.archive.getRootDirectory().equals(this.homeDirectory))) {
         File file = null;
         if (isJustArchive) {
            File candidate = new File(this.homeDirectory, path);
            if (candidate.exists()) {
               file = candidate;
               path = "";
            }
         }

         int separatorIndex = path.indexOf(33);
         if (separatorIndex != -1) {
            file = !path.startsWith("jar:file:") ? new File(this.homeDirectory, path.substring(0, separatorIndex)) : new File(path.substring("jar:file:".length(), separatorIndex));
            path = path.substring(separatorIndex + 1);
            path = this.stripLeadingSlashes(path);
         }

         if (path.equals("/") || path.equals("./") || path.equals(".")) {
            path = "";
         }

         Object archive = file != null ? new JarFileArchive(file) : this.archive;

         LinkedHashSet var7;
         try {
            Set<URL> urls = new LinkedHashSet(((Archive)archive).getClassPathUrls(this.includeByPrefix(path)));
            if (!isJustArchive && file != null && path.isEmpty()) {
               urls.add(JarUrl.create(file));
            }

            var7 = urls;
         } finally {
            if (archive != this.archive) {
               ((Archive)archive).close();
            }

         }

         return var7;
      } else {
         return Collections.emptySet();
      }
   }

   private Set<URL> getClassPathUrlsForRoot() throws IOException {
      debug.log("Adding classpath entries from root archive %s", this.archive);
      return this.archive.getClassPathUrls(JarLauncher::isLibraryFileOrClassesDirectory);
   }

   private Predicate<Archive.Entry> includeByPrefix(String prefix) {
      return (entry) -> {
         return entry.isDirectory() && entry.name().equals(prefix) || this.isArchive(entry) && entry.name().startsWith(prefix);
      };
   }

   private boolean isArchive(Archive.Entry entry) {
      return this.isArchive(entry.name());
   }

   private boolean isArchive(String name) {
      name = name.toLowerCase(Locale.ENGLISH);
      return name.endsWith(".jar") || name.endsWith(".zip");
   }

   private boolean isAbsolutePath(String root) {
      return root.contains(":") || root.startsWith("/");
   }

   private String stripLeadingSlashes(String string) {
      while(string.startsWith("/")) {
         string = string.substring(1);
      }

      return string;
   }

   public static void main(String[] args) throws Exception {
      PropertiesLauncher launcher = new PropertiesLauncher();
      args = launcher.getArgs(args);
      launcher.launch(args);
   }

   static {
      NESTED_ARCHIVE_SEPARATOR = "!" + File.separator;
      debug = DebugLogger.get(PropertiesLauncher.class);
   }

   private static record Instantiator<T>(ClassLoader parent, Class<?> type) {
      Instantiator(ClassLoader parent, String className) throws ClassNotFoundException {
         this(parent, Class.forName(className, true, parent));
      }

      private Instantiator(ClassLoader parent, Class<?> type) {
         this.parent = parent;
         this.type = type;
      }

      T constructWithoutParameters() throws Exception {
         return this.declaredConstructor().newInstance();
      }

      PropertiesLauncher.Instantiator.Using<T> declaredConstructor(Class<?>... parameterTypes) {
         return new PropertiesLauncher.Instantiator.Using(this, parameterTypes);
      }

      public ClassLoader parent() {
         return this.parent;
      }

      public Class<?> type() {
         return this.type;
      }

      private static record Using<T>(PropertiesLauncher.Instantiator<T> instantiator, Class<?>... parameterTypes) {
         private Using(PropertiesLauncher.Instantiator<T> instantiator, Class<?>... parameterTypes) {
            this.instantiator = instantiator;
            this.parameterTypes = parameterTypes;
         }

         T newInstance(Object... initargs) throws Exception {
            try {
               Constructor<?> constructor = this.instantiator.type().getDeclaredConstructor(this.parameterTypes);
               constructor.setAccessible(true);
               return constructor.newInstance(initargs);
            } catch (NoSuchMethodException var3) {
               return null;
            }
         }

         public PropertiesLauncher.Instantiator<T> instantiator() {
            return this.instantiator;
         }

         public Class<?>[] parameterTypes() {
            return this.parameterTypes;
         }
      }
   }
}
