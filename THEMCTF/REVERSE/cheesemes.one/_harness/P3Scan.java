import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.util.ArrayList;
import java.util.Comparator;
import java.util.List;

public final class P3Scan {
    record Result(char ch, double avg, int ok) {}

    public static void main(String[] args) throws Exception {
        String prefix = args.length > 0 ? args[0] : "";
        String charset = args.length > 1 ? args[1] : "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_{}";
        int rounds = args.length > 2 ? Integer.parseInt(args[2]) : 500;
        int repeats = args.length > 3 ? Integer.parseInt(args[3]) : 5;
        char filler = args.length > 4 ? args[4].charAt(0) : 'A';

        Method p3 = com.update.ctf.Challenge.class.getDeclaredMethod("checkPart3", byte[].class);
        p3.setAccessible(true);
        byte[] warm = "AAAAAAAAAAAAAAA".getBytes(StandardCharsets.UTF_8);
        for (int i = 0; i < 5000; i++) {
            p3.invoke(null, (Object) warm);
        }

        List<Result> results = new ArrayList<>();
        for (int ci = 0; ci < charset.length(); ci++) {
            char ch = charset.charAt(ci);
            char[] buf = new char[15];
            for (int i = 0; i < buf.length; i++) {
                buf[i] = filler;
            }
            for (int i = 0; i < prefix.length() && i < buf.length; i++) {
                buf[i] = prefix.charAt(i);
            }
            if (prefix.length() < buf.length) {
                buf[prefix.length()] = ch;
            }
            byte[] candidate = new String(buf).getBytes(StandardCharsets.UTF_8);

            long total = 0;
            int ok = 0;
            for (int r = 0; r < repeats; r++) {
                long start = System.nanoTime();
                for (int i = 0; i < rounds; i++) {
                    if ((Boolean) p3.invoke(null, (Object) candidate)) {
                        ok++;
                    }
                }
                total += System.nanoTime() - start;
            }
            results.add(new Result(ch, (double) total / (rounds * repeats), ok));
        }
        results.sort(Comparator.comparingDouble(Result::avg).reversed());
        for (Result result : results) {
            System.out.printf("%c %.1f ok=%d%n", result.ch(), result.avg(), result.ok());
        }
    }
}
