package org.springframework.boot.loader.ref;

import java.lang.ref.Cleaner.Cleanable;

public interface Cleaner {
   Cleaner instance = DefaultCleaner.instance;

   Cleanable register(Object obj, Runnable action);
}
