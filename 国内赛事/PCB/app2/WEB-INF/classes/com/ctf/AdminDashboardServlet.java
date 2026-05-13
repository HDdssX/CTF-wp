/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.servlet.ServletException
 *  javax.servlet.annotation.MultipartConfig
 *  javax.servlet.http.Cookie
 *  javax.servlet.http.HttpServlet
 *  javax.servlet.http.HttpServletRequest
 *  javax.servlet.http.HttpServletResponse
 *  javax.servlet.http.Part
 *  org.servlet_test.mytar.TInputStream
 *  org.servlet_test.mytar.TarEntry
 */
package com.ctf;

import com.ctf.JwtUtil;
import java.io.BufferedInputStream;
import java.io.BufferedOutputStream;
import java.io.File;
import java.io.FileOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.charset.StandardCharsets;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Objects;
import javax.servlet.ServletException;
import javax.servlet.annotation.MultipartConfig;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.Part;
import org.servlet_test.mytar.TInputStream;
import org.servlet_test.mytar.TarEntry;

@MultipartConfig(fileSizeThreshold=10240, maxFileSize=0x500000L, maxRequestSize=0x800000L)
public class AdminDashboardServlet
extends HttpServlet {
    public static String resourceDir = "uploads";

    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (AdminDashboardServlet.validateAdmin(req, resp)) {
            String path;
            switch (path = req.getPathInfo()) {
                case "/delete": {
                    this.deleteFile(req, resp);
                    break;
                }
                case "/rename": {
                    this.renameFile(req, resp);
                    break;
                }
                case "/upload": {
                    this.uploadTar(req, resp);
                    break;
                }
                case "/challengeResourceDir": {
                    this.challengeResourceDir(req, resp);
                    break;
                }
                default: {
                    resp.setStatus(404);
                    resp.getWriter().write("{\"error\":\"unknown POST path\"}");
                }
            }
        }
    }

    static boolean validateAdmin(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Cookie[] cookies = req.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                if (!"jwt".equals(cookie.getName())) continue;
                String value = cookie.getValue();
                String username = JwtUtil.validateToken(value);
                if (username == null) {
                    resp.sendError(401);
                    return false;
                }
                if (username.compareTo("admin") == 0) continue;
                resp.sendError(401);
                return false;
            }
        }
        resp.setContentType("application/json;charset=UTF-8");
        return true;
    }

    private void challengeResourceDir(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        resourceDir = req.getParameter("new-path");
        resp.setContentType("application/json; charset=UTF-8");
        resp.getWriter().write("{\"challengeResourceDir\":\"" + resourceDir + "\"}");
    }

    private void deleteFile(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String path = req.getParameter("path");
        if (path == null) {
            resp.getWriter().write("{\"error\":\"no path\"}");
            return;
        }
        File base = new File(this.getServletContext().getRealPath(resourceDir)).getCanonicalFile();
        File file = new File(base, path).getCanonicalFile();
        if (!file.getPath().startsWith(base.getPath())) {
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"error\":\"invalid path\"}");
            return;
        }
        boolean ok = this.deleteRecursive(file);
        resp.getWriter().write("{\"deleted\":" + ok + "}");
    }

    private boolean deleteRecursive(File f) {
        if (!f.exists()) {
            return false;
        }
        if (f.isDirectory()) {
            for (File c : Objects.requireNonNull(f.listFiles())) {
                this.deleteRecursive(c);
            }
        }
        return f.delete();
    }

    private void renameFile(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String oldPath = req.getParameter("oldPath");
        String newName = req.getParameter("newName");
        if (oldPath == null || newName == null) {
            resp.getWriter().write("{\"error\":\"params missing\"}");
            return;
        }
        File base = new File(this.getServletContext().getRealPath(resourceDir)).getCanonicalFile();
        File oldFile = new File(base, oldPath).getCanonicalFile();
        File newFile = new File(base, newName).getCanonicalFile();
        if (!oldFile.getPath().startsWith(base.getPath()) || !newFile.getPath().startsWith(base.getPath())) {
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"error\":\"invalid path\"}");
            return;
        }
        boolean ok = oldFile.renameTo(newFile);
        resp.getWriter().write("{\"renamed\":" + ok + "}");
    }

    private void uploadTar(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Path fileDir = Paths.get(req.getServletContext().getRealPath("tmp"), new String[0]);
        if (!fileDir.toFile().exists()) {
            fileDir.toFile().mkdirs();
        }
        resp.setContentType("application/json; charset=UTF-8");
        try {
            boolean ok;
            Part filePart = req.getPart("file");
            if (filePart == null) {
                resp.getWriter().write("{\"error\":\"no file uploaded\"}");
                return;
            }
            Path targetPath = Paths.get(this.getServletContext().getRealPath("tmp/out.tar"), new String[0]);
            try (InputStream in = filePart.getInputStream();
                 OutputStream out = Files.newOutputStream(targetPath, new OpenOption[0]);){
                int len;
                byte[] buf = new byte[8192];
                while ((len = in.read(buf)) != -1) {
                    if (new String(buf, 0, len, StandardCharsets.UTF_8).contains("\uff8e") || new String(buf, 0, len, StandardCharsets.UTF_8).contains("\uff9d")) continue;
                    out.write(buf, 0, len);
                }
            }
            String destFolder = "uploads";
            TInputStream tis = new TInputStream((InputStream)new BufferedInputStream(Files.newInputStream(targetPath, new OpenOption[0])));
            TarEntry entry = tis.getNextEntry();
            if (entry != null) {
                int count;
                byte[] data = new byte[2048];
                FileOutputStream fos = new FileOutputStream(this.getServletContext().getRealPath(destFolder) + entry.getName());
                BufferedOutputStream dest = new BufferedOutputStream(fos);
                while ((count = tis.read(data)) != -1) {
                    dest.write(data, 0, count);
                }
                System.out.println(new String(data));
                dest.flush();
                dest.close();
            }
            tis.close();
            File f = targetPath.toFile();
            if (f.exists() && f.isFile() && !(ok = f.delete())) {
                resp.getWriter().write("{\"status\":\"delete failed\"}");
                return;
            }
            resp.getWriter().write("{\"status\":\"ok\"}");
        }
        catch (Exception e) {
            resp.getWriter().write("{\"error\":\"" + e.getMessage() + "\"}");
        }
    }
}
