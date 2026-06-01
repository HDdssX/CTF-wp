package org.example;

import java.io.FileInputStream;
import java.io.ObjectInputStream;

public class VulTest {
    public static void main(String[] args) throws Exception {
        ObjectInputStream ois = new SecureObjectInputStream(new FileInputStream("test_payload.bin"));
        System.out.println(ois.readObject().toString());
    }
}
