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
 */
package com.ctf;

import com.ctf.JwtUtil;
import com.ctf.UserTransactionManager;
import java.io.IOException;
import java.nio.charset.StandardCharsets;
import javax.servlet.ServletException;
import javax.servlet.ServletOutputStream;
import javax.servlet.http.Cookie;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class LoginServlet
extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String username = req.getParameter("username");
        String password = req.getParameter("password");
        String hashed = UserTransactionManager.UserInfo.hash(password);
        UserTransactionManager.UserInfo user = UserTransactionManager.getUser(username);
        if (user != null && hashed.compareTo(user.getPasswordHash()) == 0) {
            String token = JwtUtil.generateToken(username);
            Cookie cookie = new Cookie("jwt", token);
            cookie.setHttpOnly(true);
            cookie.setPath("/");
            resp.addCookie(cookie);
            if (username.compareTo("admin") == 0) {
                resp.sendRedirect("admin.html");
                return;
            }
            resp.sendRedirect("dashboard.html");
        } else {
            resp.setContentType("text/html; charset=UTF-8");
            ServletOutputStream out = resp.getOutputStream();
            out.write("Incorrect username or password".getBytes(StandardCharsets.UTF_8));
            out.flush();
        }
    }
}
