package com.rctf.server.tool;

import java.io.Serializable;
import java.lang.reflect.InvocationHandler;
import java.lang.reflect.Method;
import java.lang.reflect.Proxy;

public class Maybe extends Proxy implements Comparable<Object>, Serializable {
   public Maybe(InvocationHandler h) {
      super(h);
   }

   public int compareTo(Object o) {
      try {
         Method method = Comparable.class.getMethod("compareTo", Object.class);
         Object result = this.h.invoke(this, method, new Object[]{o});
         return (Integer)result;
      } catch (Throwable var4) {
         throw new RuntimeException(var4);
      }
   }
}
