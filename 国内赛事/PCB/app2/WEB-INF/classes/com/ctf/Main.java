package com.ctf;

import org.apache.catalina.Context;
import org.apache.catalina.LifecycleException;
import org.apache.catalina.startup.Tomcat;

import java.io.File;

public class Main {
    public static void main(String[] args) throws LifecycleException {
        int port = 8080;
        if (args.length > 0) {
            try {
                port = Integer.parseInt(args[0]);
            } catch (NumberFormatException e) {
                System.out.println("Invalid port number, using default 8080");
            }
        }

        Tomcat tomcat = new Tomcat();
        tomcat.setPort(port);
        tomcat.getConnector();

        // 设置工作目录
        String webappDirLocation = "src/main/webapp/";
        File webappDir = new File(webappDirLocation);
        if (!webappDir.exists()) {
            webappDir = new File(".");
        }

        Context ctx = tomcat.addWebapp("", webappDir.getAbsolutePath());

        // 注册Servlets
        Tomcat.addServlet(ctx, "LoginServlet", new LoginServlet());
        ctx.addServletMappingDecoded("/api/login", "LoginServlet");

        Tomcat.addServlet(ctx, "RegisterServlet", new RegisterServlet());
        ctx.addServletMappingDecoded("/api/register", "RegisterServlet");

        Tomcat.addServlet(ctx, "DashboardServlet", new DashboardServlet());
        ctx.addServletMappingDecoded("/api/dashboard", "DashboardServlet");

        Tomcat.addServlet(ctx, "AdminDashboardServlet", new AdminDashboardServlet());
        ctx.addServletMappingDecoded("/api/admin/dashboard", "AdminDashboardServlet");

        Tomcat.addServlet(ctx, "BackUpServlet", new BackUpServlet());
        ctx.addServletMappingDecoded("/api/admin/backup", "BackUpServlet");

        System.out.println("Starting server on port " + port);
        tomcat.start();
        tomcat.getServer().await();
    }
}
