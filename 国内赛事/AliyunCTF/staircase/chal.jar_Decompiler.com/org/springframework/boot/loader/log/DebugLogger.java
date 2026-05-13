package org.springframework.boot.loader.log;

public abstract class DebugLogger {
   private static final String ENABLED_PROPERTY = "loader.debug";
   private static final DebugLogger disabled = Boolean.getBoolean("loader.debug") ? null : new DebugLogger.DisabledDebugLogger();

   public abstract void log(String message);

   public abstract void log(String message, Object arg1);

   public abstract void log(String message, Object arg1, Object arg2);

   public abstract void log(String message, Object arg1, Object arg2, Object arg3);

   public abstract void log(String message, Object arg1, Object arg2, Object arg3, Object arg4);

   public static DebugLogger get(Class<?> sourceClass) {
      return (DebugLogger)(disabled != null ? disabled : new DebugLogger.SystemErrDebugLogger(sourceClass));
   }

   private static final class SystemErrDebugLogger extends DebugLogger {
      private final String prefix;

      SystemErrDebugLogger(Class<?> sourceClass) {
         this.prefix = "LOADER: " + sourceClass + " : ";
      }

      public void log(String message) {
         this.print(message);
      }

      public void log(String message, Object arg1) {
         this.print(message.formatted(new Object[]{arg1}));
      }

      public void log(String message, Object arg1, Object arg2) {
         this.print(message.formatted(new Object[]{arg1, arg2}));
      }

      public void log(String message, Object arg1, Object arg2, Object arg3) {
         this.print(message.formatted(new Object[]{arg1, arg2, arg3}));
      }

      public void log(String message, Object arg1, Object arg2, Object arg3, Object arg4) {
         this.print(message.formatted(new Object[]{arg1, arg2, arg3, arg4}));
      }

      private void print(String message) {
         System.err.println(this.prefix + message);
      }
   }

   private static final class DisabledDebugLogger extends DebugLogger {
      public void log(String message) {
      }

      public void log(String message, Object arg1) {
      }

      public void log(String message, Object arg1, Object arg2) {
      }

      public void log(String message, Object arg1, Object arg2, Object arg3) {
      }

      public void log(String message, Object arg1, Object arg2, Object arg3, Object arg4) {
      }
   }
}
