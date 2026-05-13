/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.servlet.ServletException
 *  javax.servlet.http.HttpServlet
 *  javax.servlet.http.HttpServletRequest
 *  javax.servlet.http.HttpServletResponse
 *  org.servlet_test.mytar.TInputStream
 *  org.servlet_test.mytar.TOutputStream
 *  org.servlet_test.mytar.TarEntry
 */
package com.ctf;

import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Paths;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import org.servlet_test.mytar.TInputStream;
import org.servlet_test.mytar.TOutputStream;
import org.servlet_test.mytar.TarEntry;

public class BackUpServlet
extends HttpServlet {
    private static final String UPLOAD_DIR = "uploads";
    private static final String BACKUP_DIR = "backup";

    public void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String action = req.getPathInfo();
        if (action == null) {
            this.writeError(resp, "missing action");
            return;
        }
        String appRoot = this.getServletContext().getRealPath("/");
        File appDir = new File(appRoot);
        String parentDir = appDir.getParent();
        String key = new String(Files.readAllBytes(Paths.get(parentDir, "\uff8e\uff9d.key")));
        String inputKey = req.getParameter("key");
        if (inputKey == null) {
            this.writeError(resp, "missing key");
            return;
        }
        if (!key.equals(inputKey)) {
            this.writeError(resp, "not this key");
            return;
        }
        switch (action) {
            case "/tar": {
                this.doTar(req, resp);
                break;
            }
            case "/untar": {
                this.doUnTar(req, resp);
                break;
            }
            default: {
                this.writeError(resp, "unknown action");
            }
        }
    }

    private void doTar(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        File fileDir = Paths.get(this.getServletContext().getRealPath(BACKUP_DIR), new String[0]).toFile();
        if (!fileDir.exists()) {
            fileDir.mkdirs();
        }
        FileOutputStream dest = new FileOutputStream(this.getServletContext().getRealPath(BACKUP_DIR) + "/out.tar");
        TOutputStream out = new TOutputStream((OutputStream)new BufferedOutputStream(dest));
        File dir = new File(this.getServletContext().getRealPath(UPLOAD_DIR));
        File[] filesToTar = dir.listFiles(File::isFile);
        if (filesToTar != null) {
            for (File f : filesToTar) {
                int count;
                out.putNextEntry(new TarEntry(f, f.getName()));
                BufferedInputStream origin = new BufferedInputStream(Files.newInputStream(f.toPath(), new OpenOption[0]));
                byte[] data = new byte[2048];
                while ((count = origin.read(data)) != -1) {
                    out.write(data, 0, count);
                }
                out.flush();
                origin.close();
            }
        }
        out.close();
    }

    private void doUnTar(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        TInputStream tis = new TInputStream((InputStream)new BufferedInputStream(Files.newInputStream(Paths.get(this.getServletContext().getRealPath("backup/out.tar"), new String[0]), new OpenOption[0])));
        TarEntry entry = tis.getNextEntry();
        if (entry != null) {
            int count;
            byte[] data = new byte[2048];
            FileOutputStream fos = new FileOutputStream(this.getServletContext().getRealPath(UPLOAD_DIR) + "/" + entry.getName());
            BufferedOutputStream dest = new BufferedOutputStream(fos);
            while ((count = tis.read(data)) != -1) {
                dest.write(data, 0, count);
            }
            dest.flush();
            dest.close();
        }
        tis.close();
    }

    private void writeError(HttpServletResponse resp, String msg) throws IOException {
        resp.setStatus(400);
        this.writeJson(resp, "{\"error\":\"" + msg + "\"}");
    }

    private void writeJson(HttpServletResponse resp, String json) throws IOException {
        resp.setContentType("application/json; charset=UTF-8");
        resp.getWriter().write(json);
    }
}
