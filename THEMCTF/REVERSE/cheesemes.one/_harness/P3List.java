import java.lang.reflect.Method;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.ArrayList;
import java.util.List;

public final class P3List {
    public static void main(String[] args) throws Exception {
        Method p3 = com.update.ctf.Challenge.class.getDeclaredMethod("checkPart3", byte[].class);
        p3.setAccessible(true);
        List<String> candidates = new ArrayList<>();
        if (args.length > 0) {
            candidates.addAll(Files.readAllLines(Path.of(args[0]), StandardCharsets.UTF_8));
        }
        for (String s : candidates) {
            if (s.isBlank() || s.startsWith("#")) {
                continue;
            }
            byte[] bytes = s.getBytes(StandardCharsets.UTF_8);
            if (bytes.length == 15 && (Boolean) p3.invoke(null, (Object) bytes)) {
                System.out.println("FOUND " + s);
                return;
            }
        }
        System.out.println("not found in " + candidates.size());
    }
}
