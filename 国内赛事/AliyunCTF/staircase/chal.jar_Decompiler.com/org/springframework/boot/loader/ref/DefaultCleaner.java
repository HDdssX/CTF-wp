package org.springframework.boot.loader.ref;

import java.lang.ref.Cleaner.Cleanable;
import java.util.function.BiConsumer;

class DefaultCleaner implements Cleaner {
   static final DefaultCleaner instance = new DefaultCleaner();
   static BiConsumer<Object, Cleanable> tracker;
   private final java.lang.ref.Cleaner cleaner = java.lang.ref.Cleaner.create();

   public Cleanable register(Object obj, Runnable action) {
      Cleanable cleanable = action != null ? this.cleaner.register(obj, action) : null;
      if (tracker != null) {
         tracker.accept(obj, cleanable);
      }

      return cleanable;
   }
}
