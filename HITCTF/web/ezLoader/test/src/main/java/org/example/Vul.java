package org.example;

import java.io.FileInputStream;
import java.io.ObjectInputStream;

public class Vul {
    public static void main(String[] args) throws Exception {
        ObjectInputStream ois = new SecureObjectInputStream(new FileInputStream("payload.bin"));
        System.out.println(ois.readObject().toString());
    }
}
