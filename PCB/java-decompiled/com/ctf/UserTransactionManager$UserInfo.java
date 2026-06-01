/*
 * Decompiled with CFR 0.152.
 */
package com.ctf;

import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.Base64;

public static class UserTransactionManager.UserInfo {
    private String passwordHash;
    private String role;
    private boolean active;
    private String email;
    private String phone;

    public UserTransactionManager.UserInfo(String passwordHash) {
        this.passwordHash = passwordHash;
        this.role = "USER";
        this.active = true;
    }

    public String getPasswordHash() {
        return this.passwordHash;
    }

    public void setPasswordHash(String passwordHash) {
        this.passwordHash = passwordHash;
    }

    public String getRole() {
        return this.role;
    }

    public void setRole(String role) {
        this.role = role;
    }

    public boolean isActive() {
        return this.active;
    }

    public void setActive(boolean active) {
        this.active = active;
    }

    public String getEmail() {
        return this.email;
    }

    public void setEmail(String email) {
        this.email = email;
    }

    public String getPhone() {
        return this.phone;
    }

    public void setPhone(String phone) {
        this.phone = phone;
    }

    public static String hash(String password) {
        try {
            MessageDigest md = MessageDigest.getInstance("SHA-256");
            byte[] digest = md.digest(password.getBytes(StandardCharsets.UTF_8));
            return Base64.getEncoder().encodeToString(digest);
        }
        catch (Exception e) {
            throw new RuntimeException(e);
        }
    }
}
