package com.appaveli.service;

import java.util.List;

public class TestService {

    public String getUserById(String id) {
        // Simulate fetching user
        if (id == null || id.isEmpty()) {
            return null;
        }

        return "User_" + id;
    }

    public List<String> getAllUsers() {
        return List.of("User_1", "User_2", "User_3");
    }

    public boolean deleteUser(String id) {
        // Simulate delete operation
        System.out.println("Deleting user: " + id);
        return true;
    }

    public void createUser(String name, String email) {
        if (name == null || email == null) {
            throw new IllegalArgumentException("Name and email are required.");
        }

        System.out.println("Creating user: " + name + ", " + email);
    }
}