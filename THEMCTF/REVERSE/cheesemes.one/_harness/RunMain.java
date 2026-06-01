import java.security.Permission;
import java.io.ByteArrayInputStream;
import java.io.DataInputStream;
import java.lang.reflect.Method;
import java.lang.reflect.Field;
import java.io.PrintWriter;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.Arrays;
import javax.crypto.Cipher;
import javax.crypto.spec.GCMParameterSpec;
import javax.crypto.spec.SecretKeySpec;

public final class RunMain {
    static final class NoExit extends SecurityManager {
        @Override
        public void checkPermission(Permission perm) {
        }

        @Override
        public void checkExit(int status) {
            throw new SecurityException("exit " + status);
        }
    }

    public static void main(String[] args) throws Exception {
        System.setSecurityManager(new NoExit());
        try {
            com.update.ctf.Challenge.main(args);
        } catch (SecurityException ex) {
            System.out.println(ex.getMessage());
        } finally {
            System.setSecurityManager(null);
        }
        dumpDecodedString("part2.pre", "Xv3yznB72036iBOSEkAWseOnFoDyaPx_HoLGDguxeccOr-_EZ3nGE_WJQsJCFUamq6NHlL5mtnscjdhXCw");
        dumpDecodedString("part2.selector", "Xv3yznB72036iBOSEkAWseOnFoDyaPx_HoLGDguxeccOr-_EZ3nGE_WJQsJCFUamq6NHlA");
        dumpFfl("part2", com.update.ctf.Challenge.class,
                "ajyiv7/ome04d1e/ff8zoj/gmv3/175018dca521bdad4d58.bin",
                Path.of("_ffl_part2.txt"));
        dumpVmPack("bts.bin", Path.of("_extract/ajyiv7/ome04d1e/ff8zoj/bts.bin"), Path.of("_dump_bts"));
    }

    private static void dumpDecodedString(String label, String value) throws Exception {
        Method method = Class.forName("internal.j64mft.ajyiv").getDeclaredMethod("_jjwy8", String.class);
        method.setAccessible(true);
        String decoded = (String) method.invoke(null, value);
        byte[] bytes = decoded.getBytes(StandardCharsets.UTF_8);
        System.out.printf("%s len=%d text=%s hex=%s%n", label, bytes.length, decoded, toHex(bytes));
    }

    private static void dumpVmPack(String label, Path source, Path root) throws Exception {
        Method keyMethod = Class.forName("internal.j64mft.ajyiv").getDeclaredMethod("_bbav2", byte[].class);
        keyMethod.setAccessible(true);
        byte[] digest = (byte[]) keyMethod.invoke(null, "vm-pack-v1".getBytes(StandardCharsets.UTF_8));
        byte[] key = Arrays.copyOf(digest, 16);

        byte[] data = Files.readAllBytes(source);
        byte[] iv = Arrays.copyOfRange(data, 0, 12);
        byte[] payload = Arrays.copyOfRange(data, 12, data.length);
        Cipher cipher = Cipher.getInstance("AES/GCM/NoPadding");
        cipher.init(Cipher.DECRYPT_MODE, new SecretKeySpec(key, "AES"), new GCMParameterSpec(128, iv));
        byte[] plain = cipher.doFinal(payload);

        DataInputStream in = new DataInputStream(new ByteArrayInputStream(plain));
        int magic = in.readInt();
        int count = in.readInt();
        System.out.printf("%s magic=%08x count=%d%n", label, magic, count);
        for (int i = 0; i < count; i++) {
            int nameLength = in.readUnsignedShort();
            byte[] nameBytes = in.readNBytes(nameLength);
            String name = new String(nameBytes, StandardCharsets.UTF_8);
            int classLength = in.readInt();
            byte[] classBytes = in.readNBytes(classLength);
            Path out = root.resolve(name.replace('.', '/') + ".class");
            Files.createDirectories(out.getParent());
            Files.write(out, classBytes);
            System.out.printf("dumped %s len=%d%n", name, classLength);
        }
    }

    private static void dumpFfl(String label, Class<?> owner, String selector, Path out) throws Exception {
        Class<?> vm = Class.forName("internal.j64mft.obmwyxuh");
        Method method = vm.getDeclaredMethod("_mau4l3", Class.class, String.class);
        method.setAccessible(true);
        Object ffl = method.invoke(null, owner, selector);
        try (PrintWriter writer = new PrintWriter(Files.newBufferedWriter(out, StandardCharsets.UTF_8))) {
            writer.printf("%s %s%n", label, ffl.getClass().getName());
            dumpObject(writer, ffl, "");
        }
        System.out.println("wrote " + out);
    }

    private static void dumpObject(PrintWriter writer, Object value, String indent) throws Exception {
        if (value == null) {
            writer.println(indent + "null");
            return;
        }
        Class<?> cls = value.getClass();
        writer.println(indent + cls.getName());
        for (Field field : cls.getDeclaredFields()) {
            if (java.lang.reflect.Modifier.isStatic(field.getModifiers())) {
                continue;
            }
            field.setAccessible(true);
            Object fieldValue = field.get(value);
            writer.printf("%s%s = %s%n", indent, field.getName(), formatValue(fieldValue));
            if (fieldValue != null && fieldValue.getClass().isArray()
                    && !fieldValue.getClass().getComponentType().isPrimitive()) {
                Object[] items = (Object[]) fieldValue;
                for (int i = 0; i < items.length; i++) {
                    writer.printf("%s  [%d] %s%n", indent, i, formatValue(items[i]));
                    if (items[i] != null && items[i].getClass().getName().startsWith("internal.j64mft.obmwyxuh$")) {
                        dumpObject(writer, items[i], indent + "    ");
                    }
                }
            }
        }
    }

    private static String formatValue(Object value) {
        if (value == null) {
            return "null";
        }
        Class<?> cls = value.getClass();
        if (!cls.isArray()) {
            if (value instanceof String string) {
                return '"' + string + '"';
            }
            return String.valueOf(value);
        }
        if (value instanceof int[] array) {
            return Arrays.toString(array);
        }
        if (value instanceof byte[] array) {
            return toHex(array);
        }
        if (value instanceof long[] array) {
            return Arrays.toString(array);
        }
        if (value instanceof Object[] array) {
            return cls.getComponentType().getName() + "[" + array.length + "]";
        }
        return cls.getComponentType().getName() + "[]";
    }

    private static String toHex(byte[] bytes) {
        StringBuilder out = new StringBuilder(bytes.length * 2);
        for (byte b : bytes) {
            out.append(String.format("%02x", b & 0xff));
        }
        return out.toString();
    }
}
