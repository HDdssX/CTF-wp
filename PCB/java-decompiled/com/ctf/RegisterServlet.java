/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  javax.servlet.ServletException
 *  javax.servlet.http.HttpServlet
 *  javax.servlet.http.HttpServletRequest
 *  javax.servlet.http.HttpServletResponse
 */
package com.ctf;

import com.ctf.UserTransactionManager;
import java.io.IOException;
import javax.servlet.ServletException;
import javax.servlet.http.HttpServlet;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;

public class RegisterServlet
extends HttpServlet {
    protected void doPost(HttpServletRequest req, HttpServletResponse resp) throws ServletException, IOException {
        String username = req.getParameter("username");
        String password = req.getParameter("password");
        if (username == null || username.isEmpty() || password == null || password.isEmpty()) {
            resp.sendRedirect("register.html?error=empty");
            return;
        }
        try {
            UserTransactionManager.addUser(username, UserTransactionManager.UserInfo.hash(password));
        }
        catch (IllegalArgumentException e) {
            resp.sendRedirect("register.html?error=exists");
            return;
        }
        catch (Exception e) {
            resp.sendRedirect("register.html?error=invalid");
            return;
        }
        resp.sendRedirect("index.html?register=success");
    }
}
