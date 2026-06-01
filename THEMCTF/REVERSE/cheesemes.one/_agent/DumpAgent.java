import java.io.IOException;
import java.lang.instrument.ClassFileTransformer;
import java.lang.instrument.Instrumentation;
import java.nio.file.Files;
import java.nio.file.Path;
import java.security.ProtectionDomain;

public final class DumpAgent {
    public static void premain(String args, Instrumentation inst) {
        Path root = Path.of(args == null || args.isBlank() ? "_agent_dump" : args);
        inst.addTransformer(new ClassFileTransformer() {
            @Override
            public byte[] transform(Module module, ClassLoader loader, String className,
                    Class<?> classBeingRedefined, ProtectionDomain protectionDomain,
                    byte[] classfileBuffer) {
                if (className == null || classfileBuffer == null) {
                    return null;
                }
                if (className.startsWith("internal/")
                        || className.startsWith("com/update/ctf/")
                        || className.startsWith("ajyiv7/")) {
                    try {
                        Path out = root.resolve(className + ".class");
                        Files.createDirectories(out.getParent());
                        Files.write(out, classfileBuffer);
                    } catch (IOException ignored) {
                        // Dumping is best-effort and must not affect challenge behavior.
                    }
                }
                return null;
            }
        }, false);
    }
}
