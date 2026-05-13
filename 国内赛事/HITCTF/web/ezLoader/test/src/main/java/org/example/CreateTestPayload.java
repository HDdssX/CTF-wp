package org.example;

import java.io.FileOutputStream;
import java.io.ObjectOutputStream;

public class CreateTestPayload {
    public static void main(String[] args) throws Exception {
        String testData = "Hello from deserialization test!";
        ObjectOutputStream oos = new ObjectOutputStream(new FileOutputStream("test_payload.bin"));
        oos.writeObject(testData);
        oos.close();
        System.out.println("Created test_payload.bin with: " + testData);
    }
}
