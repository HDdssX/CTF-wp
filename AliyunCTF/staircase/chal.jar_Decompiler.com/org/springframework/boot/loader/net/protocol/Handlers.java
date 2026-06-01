package org.springframework.boot.loader.net.protocol;

import java.net.URL;
import java.net.URLStreamHandlerFactory;

public final class Handlers {
   private static final String PROTOCOL_HANDLER_PACKAGES = "java.protocol.handler.pkgs";
   private static final String PACKAGE = Handlers.class.getPackageName();

   private Handlers() {
   }

   public static void register() {
      String packages = System.getProperty("java.protocol.handler.pkgs", "");
      packages = !packages.isEmpty() && !packages.contains(PACKAGE) ? packages + "|" + PACKAGE : PACKAGE;
      System.setProperty("java.protocol.handler.pkgs", packages);
      resetCachedUrlHandlers();
   }

   private static void resetCachedUrlHandlers() {
      try {
         URL.setURLStreamHandlerFactory((URLStreamHandlerFactory)null);
      } catch (Error var1) {
      }

   }
}
