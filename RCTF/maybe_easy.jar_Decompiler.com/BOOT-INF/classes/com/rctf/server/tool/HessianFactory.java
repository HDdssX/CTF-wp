package com.rctf.server.tool;

import com.caucho.hessian.io.Hessian2Input;
import com.caucho.hessian.io.Hessian2Output;
import com.caucho.hessian.io.SerializerFactory;
import java.io.ByteArrayInputStream;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.util.Base64;
import java.util.HashSet;
import java.util.Iterator;
import java.util.Set;

public class HessianFactory extends SerializerFactory {
   private static final Set<String> WHITE_PACKAGES = new HashSet();

   HessianFactory() {
   }

   public ClassLoader getClassLoader() {
      return new HessianFactory.WhiteListClassLoader(super.getClassLoader());
   }

   public static <T> String serialize(T object) throws Exception {
      ByteArrayOutputStream byteArrayOutputStream = new ByteArrayOutputStream();
      Hessian2Output hessian2Output = new Hessian2Output(byteArrayOutputStream);
      hessian2Output.getSerializerFactory().setAllowNonSerializable(true);
      hessian2Output.writeObject(object);
      hessian2Output.flushBuffer();
      return Base64.getEncoder().encodeToString(byteArrayOutputStream.toByteArray());
   }

   public static Object deserialize(String s) throws IOException, ClassNotFoundException {
      byte[] data = Base64.getDecoder().decode(s);
      ByteArrayInputStream bis = new ByteArrayInputStream(data);
      Hessian2Input h2i = new Hessian2Input(bis);
      h2i.setSerializerFactory(new HessianFactory());
      return h2i.readObject();
   }

   static {
      WHITE_PACKAGES.add("com.rctf.server.tool.");
      WHITE_PACKAGES.add("java.util.");
      WHITE_PACKAGES.add("org.apache.commons.logging.");
      WHITE_PACKAGES.add("org.springframework.beans.");
      WHITE_PACKAGES.add("org.springframework.jndi.");
   }

   private static class WhiteListClassLoader extends ClassLoader {
      private final ClassLoader parent;

      public WhiteListClassLoader(ClassLoader parent) {
         super(parent);
         this.parent = parent;
      }

      protected Class<?> loadClass(String name, boolean resolve) throws ClassNotFoundException {
         boolean allowed = false;
         Iterator var4 = HessianFactory.WHITE_PACKAGES.iterator();

         while(var4.hasNext()) {
            String prefix = (String)var4.next();
            if (name.startsWith(prefix)) {
               allowed = true;
               break;
            }
         }

         if (!allowed) {
            throw new ClassNotFoundException("Class not allowed for deserialization: " + name);
         } else {
            return this.parent.loadClass(name);
         }
      }
   }
}
