import java.lang.reflect.Method;
import java.security.Permission;
import java.nio.charset.StandardCharsets;
import java.util.Arrays;

public final class ProbeParts {
    static final class NoExit extends SecurityManager {
        @Override public void checkPermission(Permission perm) {}
        @Override public void checkExit(int status) {
            throw new SecurityException("exit " + status);
        }
    }

    public static void main(String[] args) throws Exception {
        String flag = args.length == 0 ? "" : args[0];
        System.setSecurityManager(new NoExit());
        try {
            com.update.ctf.Challenge.main(new String[] { flag });
        } catch (SecurityException ex) {
            System.out.println("main " + ex.getMessage());
        } finally {
            System.setSecurityManager(null);
        }

        byte[] all = flag.getBytes(StandardCharsets.UTF_8);
        Class<?> cls = com.update.ctf.Challenge.class;
        Method p1 = cls.getDeclaredMethod("checkPart1", byte[].class);
        Method p2 = cls.getDeclaredMethod("checkPart2", byte[].class);
        Method p3 = cls.getDeclaredMethod("checkPart3", byte[].class);
        p1.setAccessible(true);
        p2.setAccessible(true);
        p3.setAccessible(true);
        System.out.println("len=" + all.length);
        if (all.length >= 16) {
            System.out.println("p1=" + p1.invoke(null, (Object) Arrays.copyOfRange(all, 0, 16)));
        }
        if (all.length >= 32) {
            System.out.println("p2=" + p2.invoke(null, (Object) Arrays.copyOfRange(all, 16, 32)));
        }
        if (all.length >= 47) {
            System.out.println("p3=" + p3.invoke(null, (Object) Arrays.copyOfRange(all, 32, 47)));
        }
    }
}
