import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;

public final class P3Timing {
    public static void main(String[] args) throws Exception {
        Method p3 = com.update.ctf.Challenge.class.getDeclaredMethod("checkPart3", byte[].class);
        p3.setAccessible(true);
        int rounds = args.length > 1 ? Integer.parseInt(args[1]) : 20000;
        for (int a = 0; a < args.length; a += 2) {
            String s = args[a];
            byte[] bytes = s.getBytes(StandardCharsets.UTF_8);
            if (bytes.length != 15) {
                System.out.println(s + " len=" + bytes.length);
                continue;
            }
            long start = System.nanoTime();
            int ok = 0;
            for (int i = 0; i < rounds; i++) {
                if ((Boolean) p3.invoke(null, (Object) bytes)) {
                    ok++;
                }
            }
            long elapsed = System.nanoTime() - start;
            System.out.printf("%s ok=%d avg=%.1f ns%n", s, ok, (double) elapsed / rounds);
        }
    }
}
