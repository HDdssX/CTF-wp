package org.springframework.boot.loader.launch;

import java.util.HashSet;
import java.util.Locale;
import java.util.Properties;
import java.util.Set;

final class SystemPropertyUtils {
   private static final String PLACEHOLDER_PREFIX = "${";
   private static final String PLACEHOLDER_SUFFIX = "}";
   private static final String VALUE_SEPARATOR = ":";
   private static final String SIMPLE_PREFIX = "${".substring(1);

   private SystemPropertyUtils() {
   }

   static String resolvePlaceholders(Properties properties, String text) {
      return text != null ? parseStringValue(properties, text, text, new HashSet()) : null;
   }

   private static String parseStringValue(Properties properties, String value, String current, Set<String> visitedPlaceholders) {
      StringBuilder result = new StringBuilder(current);
      int startIndex = current.indexOf("${");

      while(startIndex != -1) {
         int endIndex = findPlaceholderEndIndex(result, startIndex);
         if (endIndex == -1) {
            startIndex = -1;
         } else {
            String placeholder = result.substring(startIndex + "${".length(), endIndex);
            String originalPlaceholder = placeholder;
            if (!visitedPlaceholders.add(placeholder)) {
               throw new IllegalArgumentException("Circular placeholder reference '" + placeholder + "' in property definitions");
            }

            placeholder = parseStringValue(properties, value, placeholder, visitedPlaceholders);
            String propertyValue = resolvePlaceholder(properties, value, placeholder);
            if (propertyValue == null) {
               int separatorIndex = placeholder.indexOf(":");
               if (separatorIndex != -1) {
                  String actualPlaceholder = placeholder.substring(0, separatorIndex);
                  String defaultValue = placeholder.substring(separatorIndex + ":".length());
                  propertyValue = resolvePlaceholder(properties, value, actualPlaceholder);
                  propertyValue = propertyValue != null ? propertyValue : defaultValue;
               }
            }

            if (propertyValue != null) {
               propertyValue = parseStringValue(properties, value, propertyValue, visitedPlaceholders);
               result.replace(startIndex, endIndex + "}".length(), propertyValue);
               startIndex = result.indexOf("${", startIndex + propertyValue.length());
            } else {
               startIndex = result.indexOf("${", endIndex + "}".length());
            }

            visitedPlaceholders.remove(originalPlaceholder);
         }
      }

      return result.toString();
   }

   private static String resolvePlaceholder(Properties properties, String text, String placeholderName) {
      String propertyValue = getProperty(placeholderName, (String)null, text);
      if (propertyValue != null) {
         return propertyValue;
      } else {
         return properties != null ? properties.getProperty(placeholderName) : null;
      }
   }

   static String getProperty(String key) {
      return getProperty(key, (String)null, "");
   }

   private static String getProperty(String key, String defaultValue, String text) {
      try {
         String value = System.getProperty(key);
         value = value != null ? value : System.getenv(key);
         value = value != null ? value : System.getenv(key.replace('.', '_'));
         value = value != null ? value : System.getenv(key.toUpperCase(Locale.ENGLISH).replace('.', '_'));
         return value != null ? value : defaultValue;
      } catch (Throwable var4) {
         System.err.println("Could not resolve key '" + key + "' in '" + text + "' as system property or in environment: " + var4);
         return defaultValue;
      }
   }

   private static int findPlaceholderEndIndex(CharSequence buf, int startIndex) {
      int index = startIndex + "${".length();
      int withinNestedPlaceholder = 0;

      while(index < buf.length()) {
         if (substringMatch(buf, index, "}")) {
            if (withinNestedPlaceholder <= 0) {
               return index;
            }

            --withinNestedPlaceholder;
            index += "}".length();
         } else if (substringMatch(buf, index, SIMPLE_PREFIX)) {
            ++withinNestedPlaceholder;
            index += SIMPLE_PREFIX.length();
         } else {
            ++index;
         }
      }

      return -1;
   }

   private static boolean substringMatch(CharSequence str, int index, CharSequence substring) {
      for(int j = 0; j < substring.length(); ++j) {
         int i = index + j;
         if (i >= str.length() || str.charAt(i) != substring.charAt(j)) {
            return false;
         }
      }

      return true;
   }
}
