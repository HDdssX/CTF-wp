import java.util.Base64;

import org.apache.shiro.crypto.AesCipherService;
import org.apache.shiro.subject.SimplePrincipalCollection;
import org.apache.shiro.io.DefaultSerializer;

public class GenShiroCookie {
    public static void main(String[] args) {
        if (args.length != 1) {
            System.err.println("Usage: GenShiroCookie <base64-key>");
            System.exit(1);
        }

        byte[] key = Base64.getDecoder().decode(args[0]);
        SimplePrincipalCollection spc = new SimplePrincipalCollection();
        byte[] serialized = new DefaultSerializer<SimplePrincipalCollection>().serialize(spc);
        AesCipherService aes = new AesCipherService();
        byte[] encrypted = aes.encrypt(serialized, key).getBytes();
        System.out.println(Base64.getEncoder().encodeToString(encrypted));
    }
}
