import java.io.IOException;
import java.io.InputStream;
import java.io.ObjectInputStream;
import java.io.ObjectStreamClass;

public class SecureObjectInputStream extends ObjectInputStream {
    static String[] blacklist = new String[] { "com.sun.org.apache.xalan.internal.xsltc.trax.TemplatesImpl",
            "com.fasterxml.jackson.databind.node.POJONode", "javax.management.BadAttributeValueExpException",
            "javax.swing.event.EventListenerList", "java.security.SignedObject" };

    public SecureObjectInputStream(InputStream in) throws IOException {
        super(in);
    }

    protected Class<?> resolveClass(ObjectStreamClass desc) throws IOException, ClassNotFoundException {
        // String name = desc.getName();

        // for(String black : blacklist) {
        // if (name.equals(black)) {
        // System.out.println("Invalid:" + desc.getName());
        // throw new ClassNotFoundException(desc.getName());
        // }
        // }

        return super.resolveClass(desc);
    }
}
