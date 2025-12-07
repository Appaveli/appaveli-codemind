

#include <iostream>
#include <string>
#include <cstring>
#include <vector>
#include <cstdlib>

using namespace std;

// Global state everywhere
char* GLOBAL_PASSWORD = nullptr;
string GLOBAL_USERNAME;

// Super fake "database" lookup (SQL injection-style string building)
string buildUserQuery(const string& username) {
    // string concatenation with untrusted input
    string query = "SELECT * FROM users WHERE username = '" + username + "';";
    return query;
}

// Horrible password handling
void setPassword(const string& pwd) {
    // fixed-size buffer, no length check
    GLOBAL_PASSWORD = new char[8]; // way too small
    strcpy(GLOBAL_PASSWORD, pwd.c_str());  // possible overflow
}

// Simulated "login" with multiple issues
bool login(const string& username, const string& password) {
    // SQL-injection-like query
    string query = buildUserQuery(username);
    cout << "[DEBUG] Running query: " << query << endl; // logs sensitive stuff

    // pretend we "fetched" a password from DB and compare plaintext
    string storedPassword = "secret"; // hardcoded

    if (password == storedPassword) {
        GLOBAL_USERNAME = username;
        setPassword(password); // store plaintext password globally
        return true;
    }
    return false;
}

// Command injection style function
void pingHost(const string& host) {
    // No validation, directly builds a shell command
    string cmd = "ping -c 1 " + host;
    cout << "[DEBUG] Executing: " << cmd << endl;
    system(cmd.c_str()); // potential command injection
}

// Very unsafe buffer usage
void readUserMessage() {
    char buffer[16]; // tiny buffer
    cout << "Enter a short message: ";
    // operator>> stops at whitespace but can still overflow for long input
    cin >> buffer; // no bounds checking
    cout << "You typed: " << buffer << endl;
}

// Bad manual memory management & use-after-free
void badVectorUsage() {
    int* data = new int[5];
    for (int i = 0; i <= 5; ++i) { // off-by-one (i <= 5 instead of i < 5)
        data[i] = i * 10;          // writes out of bounds
    }

    delete[] data;

    // use-after-free
    cout << "Data[0] after delete: " << data[0] << endl;

    // double delete
    delete[] data;
}

// More nonsense with references to local variables
int& getBadReference() {
    int value = 42;
    return value; // returning reference to local variable
}

int main() {
    cout << "=== Insecure C++ Demo ===" << endl;

    string username;
    string password;

    cout << "Username: ";
    cin >> username;

    cout << "Password: ";
    cin >> password;

    if (login(username, password)) {
        cout << "Welcome, " << GLOBAL_USERNAME << endl;
        cout << "Stored password (plaintext): " << GLOBAL_PASSWORD << endl;
    } else {
        cout << "Invalid credentials" << endl;
    }

    // Dangerous network command
    string host;
    cout << "Enter host to ping: ";
    cin >> host;
    pingHost(host);

    // Buffer overflow demo
    readUserMessage();

    // Memory bugs
    badVectorUsage();

    // Dangling reference demo
    int& ref = getBadReference();
    cout << "Bad reference value: " << ref << endl;

    // Leak: we never delete GLOBAL_PASSWORD on success if program exits early
    // (and it's also too small and unsafe to begin with)

    return 0;
}