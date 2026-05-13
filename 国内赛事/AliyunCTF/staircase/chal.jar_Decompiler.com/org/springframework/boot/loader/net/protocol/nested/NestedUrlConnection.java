package org.springframework.boot.loader.net.protocol.nested;

import java.io.File;
import java.io.FilePermission;
import java.io.FilterInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.lang.ref.Cleaner.Cleanable;
import java.net.MalformedURLException;
import java.net.URL;
import java.net.URLConnection;
import java.nio.file.Files;
import java.security.Permission;
import java.time.Instant;
import java.time.ZoneId;
import java.time.format.DateTimeFormatter;
import java.util.Collections;
import java.util.Iterator;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;
import java.util.Map.Entry;
import org.springframework.boot.loader.ref.Cleaner;

class NestedUrlConnection extends URLConnection {
   private static final DateTimeFormatter RFC_1123_DATE_TIME;
   private static final String CONTENT_TYPE = "x-java/jar";
   private final NestedUrlConnectionResources resources;
   private final Cleanable cleanup;
   private long lastModified;
   private FilePermission permission;
   private Map<String, List<String>> headerFields;

   NestedUrlConnection(URL url) throws MalformedURLException {
      this(url, Cleaner.instance);
   }

   NestedUrlConnection(URL url, Cleaner cleaner) throws MalformedURLException {
      super(url);
      this.lastModified = -1L;
      NestedLocation location = this.parseNestedLocation(url);
      this.resources = new NestedUrlConnectionResources(location);
      this.cleanup = cleaner.register(this, this.resources);
   }

   private NestedLocation parseNestedLocation(URL url) throws MalformedURLException {
      try {
         return NestedLocation.parse(url.getPath());
      } catch (IllegalArgumentException var3) {
         throw new MalformedURLException(var3.getMessage());
      }
   }

   public String getHeaderField(String name) {
      List<String> values = (List)this.getHeaderFields().get(name);
      return values != null && !values.isEmpty() ? (String)values.get(0) : null;
   }

   public String getHeaderField(int n) {
      Entry<String, List<String>> entry = this.getHeaderEntry(n);
      List<String> values = entry != null ? (List)entry.getValue() : null;
      return values != null && !values.isEmpty() ? (String)values.get(0) : null;
   }

   public String getHeaderFieldKey(int n) {
      Entry<String, List<String>> entry = this.getHeaderEntry(n);
      return entry != null ? (String)entry.getKey() : null;
   }

   private Entry<String, List<String>> getHeaderEntry(int n) {
      Iterator<Entry<String, List<String>>> iterator = this.getHeaderFields().entrySet().iterator();
      Entry<String, List<String>> entry = null;

      for(int i = 0; i < n; ++i) {
         entry = !iterator.hasNext() ? null : (Entry)iterator.next();
      }

      return entry;
   }

   public Map<String, List<String>> getHeaderFields() {
      try {
         this.connect();
      } catch (IOException var6) {
         return Collections.emptyMap();
      }

      Map<String, List<String>> headerFields = this.headerFields;
      if (headerFields == null) {
         Map<String, List<String>> headerFields = new LinkedHashMap();
         long contentLength = this.getContentLengthLong();
         long lastModified = this.getLastModified();
         if (contentLength > 0L) {
            headerFields.put("content-length", List.of(String.valueOf(contentLength)));
         }

         if (this.getLastModified() > 0L) {
            headerFields.put("last-modified", List.of(RFC_1123_DATE_TIME.format(Instant.ofEpochMilli(lastModified))));
         }

         headerFields = Collections.unmodifiableMap(headerFields);
         this.headerFields = headerFields;
      }

      return headerFields;
   }

   public int getContentLength() {
      long contentLength = this.getContentLengthLong();
      return contentLength <= 2147483647L ? (int)contentLength : -1;
   }

   public long getContentLengthLong() {
      try {
         this.connect();
         return this.resources.getContentLength();
      } catch (IOException var2) {
         return -1L;
      }
   }

   public String getContentType() {
      return "x-java/jar";
   }

   public long getLastModified() {
      if (this.lastModified == -1L) {
         try {
            this.lastModified = Files.getLastModifiedTime(this.resources.getLocation().path()).toMillis();
         } catch (IOException var2) {
            this.lastModified = 0L;
         }
      }

      return this.lastModified;
   }

   public Permission getPermission() throws IOException {
      if (this.permission == null) {
         File file = this.resources.getLocation().path().toFile();
         this.permission = new FilePermission(file.getCanonicalPath(), "read");
      }

      return this.permission;
   }

   public InputStream getInputStream() throws IOException {
      this.connect();
      return new NestedUrlConnection.ConnectionInputStream(this.resources.getInputStream());
   }

   public void connect() throws IOException {
      if (!this.connected) {
         this.resources.connect();
         this.connected = true;
      }
   }

   static {
      RFC_1123_DATE_TIME = DateTimeFormatter.RFC_1123_DATE_TIME.withZone(ZoneId.of("GMT"));
   }

   class ConnectionInputStream extends FilterInputStream {
      private volatile boolean closing;

      ConnectionInputStream(InputStream in) {
         super(in);
      }

      public void close() throws IOException {
         if (!this.closing) {
            this.closing = true;

            try {
               super.close();
            } finally {
               try {
                  NestedUrlConnection.this.cleanup.clean();
               } catch (UncheckedIOException var7) {
                  throw var7.getCause();
               }
            }

         }
      }
   }
}
