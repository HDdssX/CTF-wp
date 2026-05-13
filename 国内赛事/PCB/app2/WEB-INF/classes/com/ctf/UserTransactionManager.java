/*
 * Decompiled with CFR 0.152.
 * 
 * Could not load the following classes:
 *  io.jsonwebtoken.SignatureAlgorithm
 *  io.jsonwebtoken.security.Keys
 */
package com.ctf;

import io.jsonwebtoken.SignatureAlgorithm;
import io.jsonwebtoken.security.Keys;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.ArrayList;
import java.util.Base64;
import java.util.Collections;
import java.util.Date;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.UUID;
import java.util.function.Predicate;

public class UserTransactionManager {
    private static final Map<String, UserInfo> users = new HashMap<String, UserInfo>();
    private static Map<String, UserInfo> backup = null;
    private static boolean inTransaction = false;
    private static final List<TransactionListener> listeners = new ArrayList<TransactionListener>();
    private static final List<String> operationLogs = new ArrayList<String>();

    private static void begin() {
        if (inTransaction) {
            throw new IllegalStateException("Nested transactions are not supported");
        }
        backup = UserTransactionManager.deepCopyUsers();
        inTransaction = true;
        UserTransactionManager.notifyBegin();
    }

    private static void commit() {
        backup = null;
        inTransaction = false;
        UserTransactionManager.notifyCommit();
    }

    private static void rollback() {
        users.clear();
        users.putAll(backup);
        backup = null;
        inTransaction = false;
        UserTransactionManager.notifyRollback();
    }

    private static void doTransaction(Runnable action) {
        UserTransactionManager.begin();
        try {
            action.run();
            UserTransactionManager.commit();
        }
        catch (RuntimeException e) {
            UserTransactionManager.rollback();
            throw e;
        }
    }

    private static Map<String, UserInfo> deepCopyUsers() {
        HashMap<String, UserInfo> copy = new HashMap<String, UserInfo>();
        for (Map.Entry<String, UserInfo> entry : users.entrySet()) {
            UserInfo u = entry.getValue();
            UserInfo newU = new UserInfo(u.getPasswordHash());
            newU.setRole(u.getRole());
            newU.setActive(u.isActive());
            newU.setEmail(u.getEmail());
            newU.setPhone(u.getPhone());
            copy.put(entry.getKey(), newU);
        }
        return copy;
    }

    public void addTransactionListener(TransactionListener listener) {
        listeners.add(listener);
    }

    private static void notifyBegin() {
        listeners.forEach(TransactionListener::onBegin);
        UserTransactionManager.log("Transaction begin");
    }

    private static void notifyCommit() {
        listeners.forEach(TransactionListener::onCommit);
        UserTransactionManager.log("Transaction commit");
    }

    private static void notifyRollback() {
        listeners.forEach(TransactionListener::onRollback);
        UserTransactionManager.log("Transaction rollback");
    }

    private static void log(String msg) {
        operationLogs.add(new Date() + " - " + msg);
    }

    public List<String> getLogs() {
        return Collections.unmodifiableList(operationLogs);
    }

    public static void addUser(String username, String passwordHash) {
        UserTransactionManager.doTransaction(() -> {
            if (users.containsKey(username)) {
                throw new IllegalArgumentException("Username already exists");
            }
            users.put(username, new UserInfo(passwordHash));
            UserTransactionManager.log("User added: " + username);
        });
    }

    public static void deleteUser(String username) {
        UserTransactionManager.doTransaction(() -> {
            if (!users.containsKey(username)) {
                throw new IllegalArgumentException("User not found");
            }
            users.remove(username);
            UserTransactionManager.log("User deleted: " + username);
        });
    }

    public static void updatePassword(String username, String newPasswordHash) {
        UserTransactionManager.doTransaction(() -> {
            UserInfo u = users.get(username);
            if (u == null) {
                throw new IllegalArgumentException("User not found");
            }
            u.setPasswordHash(newPasswordHash);
            UserTransactionManager.log("Password updated for: " + username);
        });
    }

    public static void renameUser(String oldName, String newName) {
        UserTransactionManager.doTransaction(() -> {
            if (!users.containsKey(oldName)) {
                throw new IllegalArgumentException("Old username not found");
            }
            if (users.containsKey(newName)) {
                throw new IllegalArgumentException("New username already exists");
            }
            UserInfo info = users.remove(oldName);
            users.put(newName, info);
            UserTransactionManager.log("User renamed from " + oldName + " to " + newName);
        });
    }

    public static void resetPassword(String username) {
        UserTransactionManager.doTransaction(() -> {
            UserInfo u = users.get(username);
            if (u == null) {
                throw new IllegalArgumentException("User not found");
            }
            String newPwd = UUID.randomUUID().toString();
            u.setPasswordHash(newPwd);
            UserTransactionManager.log("Password reset for " + username);
        });
    }

    public static void setUserRole(String username, String role) {
        UserTransactionManager.doTransaction(() -> {
            UserInfo u = users.get(username);
            if (u == null) {
                throw new IllegalArgumentException("User not found");
            }
            u.setRole(role);
            UserTransactionManager.log("Role changed for " + username + " -> " + role);
        });
    }

    public static void setUserActive(String username, boolean active) {
        UserTransactionManager.doTransaction(() -> {
            UserInfo u = users.get(username);
            if (u == null) {
                throw new IllegalArgumentException("User not found");
            }
            u.setActive(active);
            UserTransactionManager.log("User active status updated: " + username + " -> " + active);
        });
    }

    public static void updateEmail(String username, String email) {
        UserTransactionManager.doTransaction(() -> {
            UserInfo u = users.get(username);
            if (u == null) {
                throw new IllegalArgumentException("User not found");
            }
            u.setEmail(email);
            UserTransactionManager.log("Email updated: " + username);
        });
    }

    public static void updatePhone(String username, String phone) {
        UserTransactionManager.doTransaction(() -> {
            UserInfo u = users.get(username);
            if (u == null) {
                throw new IllegalArgumentException("User not found");
            }
            u.setPhone(phone);
            UserTransactionManager.log("Phone updated: " + username);
        });
    }

    public static void addUsersBatch(Map<String, String> userMap) {
        UserTransactionManager.doTransaction(() -> {
            for (String name2 : userMap.keySet()) {
                if (!users.containsKey(name2)) continue;
                throw new IllegalArgumentException("Duplicate user: " + name2);
            }
            userMap.forEach((name, pwd) -> users.put((String)name, new UserInfo((String)pwd)));
            UserTransactionManager.log("Batch add users: " + userMap.keySet());
        });
    }

    public static void deleteUsersBatch(List<String> names) {
        UserTransactionManager.doTransaction(() -> {
            for (String n : names) {
                if (users.containsKey(n)) continue;
                throw new IllegalArgumentException("User not found: " + n);
            }
            names.forEach(users::remove);
            UserTransactionManager.log("Batch delete users: " + names);
        });
    }

    public static List<String> searchUsers(Predicate<UserInfo> filter) {
        ArrayList<String> result = new ArrayList<String>();
        for (Map.Entry<String, UserInfo> e : users.entrySet()) {
            if (!filter.test(e.getValue())) continue;
            result.add(e.getKey());
        }
        return result;
    }

    public static List<String> searchByRole(String role) {
        return UserTransactionManager.searchUsers(u -> role.equals(u.getRole()));
    }

    public static List<String> searchInactiveUsers() {
        return UserTransactionManager.searchUsers(u -> !u.isActive());
    }

    public static List<String> searchByEmailDomain(String domain) {
        return UserTransactionManager.searchUsers(u -> u.getEmail() != null && u.getEmail().endsWith(domain));
    }

    public static String exportAsJson() {
        StringBuilder sb = new StringBuilder();
        sb.append("{\n  \"users\": [\n");
        int i = 0;
        for (Map.Entry<String, UserInfo> e : users.entrySet()) {
            UserInfo u = e.getValue();
            sb.append("    {\n").append("      \"username\": \"").append(e.getKey()).append("\",\n").append("      \"password\": \"").append(u.getPasswordHash()).append("\",\n").append("      \"role\": \"").append(u.getRole()).append("\",\n").append("      \"active\": ").append(u.isActive()).append(",\n").append("      \"email\": \"").append(u.getEmail()).append("\",\n").append("      \"phone\": \"").append(u.getPhone()).append("\"\n").append("    }");
            if (++i < users.size()) {
                sb.append(",");
            }
            sb.append("\n");
        }
        sb.append("  ]\n}\n");
        UserTransactionManager.log("Exported JSON");
        return sb.toString();
    }

    public static UserInfo getUser(String username) {
        return users.get(username);
    }

    public static Map<String, UserInfo> getAllUsers() {
        return Collections.unmodifiableMap(users);
    }

    static {
        users.put("admin", new UserInfo(UserInfo.hash(String.valueOf(Keys.secretKeyFor((SignatureAlgorithm)SignatureAlgorithm.HS256)))));
    }

    public static class UserInfo {
        private String passwordHash;
        private String role;
        private boolean active;
        private String email;
        private String phone;

        public UserInfo(String passwordHash) {
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

    public static interface TransactionListener {
        public void onBegin();

        public void onCommit();

        public void onRollback();
    }
}
