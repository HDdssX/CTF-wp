/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.servlet.ServletException
 *  javax.servlet.ServletOutputStream
 *  javax.servlet.http.Cookie
 *  javax.servlet.http.HttpServlet
 *  javax.servlet.http.HttpServletRequest
 *  javax.servlet.http.HttpServletResponse
 *  javax.servlet.http.Part
 *  org.json.JSONArray
 *  org.json.JSONObject
 */
package com.ctf;

import com.ctf.AdminDashboardServlet;
import com.ctf.JwtUtil;
import java.io.File;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.net.URLEncoder;
import java.nio.file.Files;
import java.nio.file.OpenOption;
import java.util.ArrayList;
import java.util.List;
import java.util.Objects;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import javax.servlet.http.Part;
import org.json.JSONArray;
import org.json.JSONObject;

public class DashboardServlet
extends HttpServlet {
    protected void doGet(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (DashboardServlet.validateLogin(req, resp)) {
            String path;
            switch (path = req.getPathInfo()) {
                case "/list": {
                    this.listFiles(req, resp);
                    break;
                }
                case "/download": {
                    this.downloadFile(req, resp);
                    break;
                }
                case "/stats": {
                    this.getStats(req, resp);
                    break;
                }
                case "/recent": {
                    this.getRecent(req, resp);
                    break;
                }
                default: {
                    resp.setStatus(404);
                    resp.getWriter().write("{\"error\":\"unknown GET path\"}");
                }
            }
        }
    }

    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        if (DashboardServlet.validateLogin(req, resp)) {
            String path = req.getPathInfo();
            if (path.equals("/upload")) {
                this.uploadFile(req, resp);
            } else {
                resp.setStatus(404);
                resp.getWriter().write("{\"error\":\"unknown POST path\"}");
            }
        }
    }

    static boolean validateLogin(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        Cookie[] cookies = req.getCookies();
        if (cookies != null) {
            for (Cookie cookie : cookies) {
                String value;
                if (!"jwt".equals(cookie.getName()) || JwtUtil.validateToken(value = cookie.getValue()) != null) continue;
                resp.sendError(401);
                return false;
            }
        }
        resp.setContentType("application/json;charset=UTF-8");
        return true;
    }

    private boolean validatePath(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String path = req.getParameter("path");
        if (path == null) {
            resp.getWriter().write("{\"error\":\"no path\"}");
            return false;
        }
        File base = new File(this.getServletContext().getRealPath(AdminDashboardServlet.resourceDir)).getCanonicalFile();
        File file = new File(base, path).getCanonicalFile();
        if (!file.getPath().startsWith(base.getPath())) {
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"error\":\"invalid path\"}");
            return false;
        }
        return true;
    }

    private void listFiles(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        File base = new File(this.getServletContext().getRealPath(AdminDashboardServlet.resourceDir));
        System.out.println(base.getPath());
        JSONArray arr = this.scanDir(base, base);
        resp.getWriter().write(arr.toString());
    }

    private JSONArray scanDir(File root, File current) {
        JSONArray arr = new JSONArray();
        File[] files = current.listFiles();
        if (files == null) {
            return arr;
        }
        for (File f : files) {
            JSONObject obj = new JSONObject();
            obj.put("name", (Object)f.getName());
            obj.put("isDir", f.isDirectory());
            obj.put("path", (Object)root.toPath().relativize(f.toPath()).toString());
            obj.put("size", f.isFile() ? f.length() : 0L);
            obj.put("lastModified", f.lastModified());
            if (f.isDirectory()) {
                obj.put("children", (Object)this.scanDir(root, f));
            }
            arr.put((Object)obj);
        }
        return arr;
    }

    private void uploadFile(HttpServletRequest req, HttpServletResponse resp) throws IOException, ServletException {
        Part part = req.getPart("file");
        if (part == null) {
            resp.getWriter().write("{\"error\":\"no file\"}");
            return;
        }
        File base = new File(this.getServletContext().getRealPath(AdminDashboardServlet.resourceDir)).getCanonicalFile();
        File target = new File(base, part.getSubmittedFileName()).getCanonicalFile();
        System.out.println(target.toPath());
        if (!target.getParentFile().toPath().startsWith(base.toPath())) {
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"error\":\"invalid path\"}");
            return;
        }
        try (InputStream in = part.getInputStream();
             OutputStream out = Files.newOutputStream(target.toPath(), new OpenOption[0]);){
            in.transferTo(out);
        }
        resp.getWriter().write("{\"upload\":\"ok\",\"filename\":\"" + target.getName() + "\"}");
    }

    private void downloadFile(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        String path = req.getParameter("path");
        if (path == null) {
            resp.getWriter().write("{\"error\":\"no path\"}");
            return;
        }
        File base = new File(this.getServletContext().getRealPath("uploads")).getCanonicalFile();
        File file = new File(base, path).getCanonicalFile();
        if (!file.getPath().startsWith(base.getPath())) {
            resp.setContentType("application/json; charset=UTF-8");
            resp.getWriter().write("{\"error\":\"invalid path\"}");
            return;
        }
        resp.setContentType("application/octet-stream");
        resp.setHeader("Content-Disposition", "attachment;filename=" + URLEncoder.encode(file.getName(), "UTF-8"));
        try (InputStream in = Files.newInputStream(file.toPath(), new OpenOption[0]);
             ServletOutputStream out = resp.getOutputStream();){
            in.transferTo((OutputStream)out);
        }
    }

    private void getStats(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        File base = new File(this.getServletContext().getRealPath(AdminDashboardServlet.resourceDir));
        Stats s = new Stats();
        this.computeStats(base, s);
        JSONObject obj = new JSONObject();
        obj.put("files", s.files);
        obj.put("folders", s.folders);
        obj.put("size", s.size);
        resp.getWriter().write(obj.toString());
    }

    private void computeStats(File f, Stats s) {
        if (!f.exists()) {
            return;
        }
        if (f.isDirectory()) {
            ++s.folders;
            for (File c : Objects.requireNonNull(f.listFiles())) {
                this.computeStats(c, s);
            }
        } else {
            ++s.files;
            s.size += f.length();
        }
    }

    private void getRecent(HttpServletRequest req, HttpServletResponse resp) throws IOException {
        File base = new File(this.getServletContext().getRealPath(AdminDashboardServlet.resourceDir));
        ArrayList<File> list = new ArrayList<File>();
        this.collect(base, list);
        list.sort((a, b) -> Long.compare(b.lastModified(), a.lastModified()));
        JSONArray arr = new JSONArray();
        for (int i = 0; i < Math.min(10, list.size()); ++i) {
            File f = (File)list.get(i);
            JSONObject obj = new JSONObject();
            obj.put("name", (Object)f.getName());
            obj.put("path", (Object)base.toPath().relativize(f.toPath()).toString());
            obj.put("lastModified", f.lastModified());
            obj.put("size", f.length());
            arr.put((Object)obj);
        }
        resp.getWriter().write(arr.toString());
    }

    private void collect(File f, List<File> list) {
        if (!f.exists()) {
            return;
        }
        for (File c : Objects.requireNonNull(f.listFiles())) {
            if (c.isFile()) {
                list.add(c);
            }
            if (!c.isDirectory()) continue;
            this.collect(c, list);
        }
    }

    private static class Stats {
        long files = 0L;
        long folders = 0L;
        long size = 0L;

        private Stats() {
        }
    }
}
