/*
 * Decompiled with CFR 0.152.
 */
package com.ctf;

public static interface UserTransactionManager.TransactionListener {
    public void onBegin();

    public void onCommit();

    public void onRollback();
}
