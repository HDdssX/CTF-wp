package org.springframework.boot.loader.jar;

import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.UncheckedIOException;
import java.util.ArrayDeque;
import java.util.Collections;
import java.util.Deque;
import java.util.Iterator;
import java.util.List;
import java.util.Set;
import java.util.WeakHashMap;
import java.util.zip.Inflater;
import org.springframework.boot.loader.zip.ZipContent;

class NestedJarFileResources implements Runnable {
   private static final int INFLATER_CACHE_LIMIT = 20;
   private ZipContent zipContent;
   private final Set<InputStream> inputStreams = Collections.newSetFromMap(new WeakHashMap());
   private Deque<Inflater> inflaterCache = new ArrayDeque();

   NestedJarFileResources(File file, String nestedEntryName) throws IOException {
      this.zipContent = ZipContent.open(file.toPath(), nestedEntryName);
   }

   ZipContent zipContent() {
      return this.zipContent;
   }

   void addInputStream(InputStream inputStream) {
      synchronized(this.inputStreams) {
         this.inputStreams.add(inputStream);
      }
   }

   void removeInputStream(InputStream inputStream) {
      synchronized(this.inputStreams) {
         this.inputStreams.remove(inputStream);
      }
   }

   Runnable createInflatorCleanupAction(Inflater inflater) {
      return () -> {
         this.endOrCacheInflater(inflater);
      };
   }

   Inflater getOrCreateInflater() {
      Deque<Inflater> inflaterCache = this.inflaterCache;
      if (inflaterCache != null) {
         synchronized(inflaterCache) {
            Inflater inflater = (Inflater)this.inflaterCache.poll();
            if (inflater != null) {
               return inflater;
            }
         }
      }

      return new Inflater(true);
   }

   private void endOrCacheInflater(Inflater inflater) {
      Deque<Inflater> inflaterCache = this.inflaterCache;
      if (inflaterCache != null) {
         synchronized(inflaterCache) {
            if (this.inflaterCache == inflaterCache && inflaterCache.size() < 20) {
               inflater.reset();
               this.inflaterCache.add(inflater);
               return;
            }
         }
      }

      inflater.end();
   }

   public void run() {
      this.releaseAll();
   }

   private void releaseAll() {
      IOException exceptionChain = null;
      exceptionChain = this.releaseInflators(exceptionChain);
      exceptionChain = this.releaseInputStreams(exceptionChain);
      exceptionChain = this.releaseZipContent(exceptionChain);
      if (exceptionChain != null) {
         throw new UncheckedIOException(exceptionChain);
      }
   }

   private IOException releaseInflators(IOException exceptionChain) {
      Deque<Inflater> inflaterCache = this.inflaterCache;
      if (inflaterCache != null) {
         try {
            synchronized(inflaterCache) {
               inflaterCache.forEach(Inflater::end);
            }
         } finally {
            this.inflaterCache = null;
         }
      }

      return exceptionChain;
   }

   private IOException releaseInputStreams(IOException exceptionChain) {
      synchronized(this.inputStreams) {
         Iterator var3 = List.copyOf(this.inputStreams).iterator();

         while(var3.hasNext()) {
            InputStream inputStream = (InputStream)var3.next();

            try {
               inputStream.close();
            } catch (IOException var7) {
               exceptionChain = this.addToExceptionChain(exceptionChain, var7);
            }
         }

         this.inputStreams.clear();
         return exceptionChain;
      }
   }

   private IOException releaseZipContent(IOException exceptionChain) {
      ZipContent zipContent = this.zipContent;
      if (zipContent != null) {
         try {
            zipContent.close();
         } catch (IOException var7) {
            exceptionChain = this.addToExceptionChain(exceptionChain, var7);
         } finally {
            this.zipContent = null;
         }
      }

      return exceptionChain;
   }

   private IOException addToExceptionChain(IOException exceptionChain, IOException ex) {
      if (exceptionChain != null) {
         exceptionChain.addSuppressed(ex);
         return exceptionChain;
      } else {
         return ex;
      }
   }
}
