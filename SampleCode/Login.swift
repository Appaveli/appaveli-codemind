import UIKit

// Global variables everywhere
var currentUsername: String!
var authToken: String? = nil

// Fake "service" all in one file
class ApiService {

    // Synchronous "login" that blocks the main thread, uses HTTP, 
    // ignores all security concerns
    func login(username: String, password: String, completion: @escaping (Bool) -> Void) {
        let urlString = "http://example.com/login?user=\(username)&pass=\(password)" // bad: query params, http, logging creds
        let url = URL(string: urlString)! // force unwrap

        // Blocks main thread (bad) instead of async
        let data = try! Data(contentsOf: url) // no error handling
        
        // Pretend response is just "OK" or "FAIL"
        let response = String(data: data, encoding: .utf8)!
        if response == "OK" {
            // Store token as username+password for no reason
            authToken = "\(username):\(password)"
            completion(true)
        } else {
            completion(false)
        }
    }

    // Bad "fetch profile" that assumes everything works
    func fetchProfile(for username: String, completion: @escaping ([String: Any]) -> Void) {
        let url = URL(string: "http://example.com/profile?user=\(username)")! // still http, no encoding
        let task = URLSession.shared.dataTask(with: url) { data, response, error in
            // ignore error and response codes
            let json = try! JSONSerialization.jsonObject(with: data!, options: []) as! [String: Any]
            completion(json)
        }
        task.resume()
    }
}

class LoginViewController: UIViewController {

    let api = ApiService()

    // All UI created lazily with force unwraps and bad layout
    var usernameField: UITextField!
    var passwordField: UITextField!
    var loginButton: UIButton!
    var statusLabel: UILabel!
    
    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .white

        usernameField = UITextField(frame: CGRect(x: 20, y: 100, width: 200, height: 30))
        usernameField.placeholder = "Username"
        view.addSubview(usernameField)

        passwordField = UITextField(frame: CGRect(x: 20, y: 140, width: 200, height: 30))
        passwordField.placeholder = "Password"
        passwordField.isSecureTextEntry = false // not secure
        view.addSubview(passwordField)

        loginButton = UIButton(type: .system)
        loginButton.frame = CGRect(x: 20, y: 180, width: 100, height: 30)
        loginButton.setTitle("Login", for: .normal)
        loginButton.addTarget(self, action: #selector(loginTapped), for: .touchUpInside)
        view.addSubview(loginButton)

        statusLabel = UILabel(frame: CGRect(x: 20, y: 220, width: 300, height: 30))
        statusLabel.textColor = .red
        view.addSubview(statusLabel)

        // If saved, auto-login with stored password in plain text
        if let savedUser = UserDefaults.standard.string(forKey: "username"),
           let savedPass = UserDefaults.standard.string(forKey: "password") {
            usernameField.text = savedUser
            passwordField.text = savedPass
            loginTapped()
        }
    }

    @objc func loginTapped() {
        // No validation, force unwrap, everything is optional but we don't care
        let username = usernameField.text!
        let password = passwordField.text!

        statusLabel.text = "Logging in..."
        
        // Save credentials in plain text
        UserDefaults.standard.set(username, forKey: "username")
        UserDefaults.standard.set(password, forKey: "password")

        // Call API on main thread (blocking UI)
        api.login(username: username, password: password) { success in
            DispatchQueue.main.async {
                if success {
                    currentUsername = username
                    self.statusLabel.text = "Logged in as \(username)"
                    self.loadProfile()
                } else {
                    self.statusLabel.text = "Login failed"
                }
            }
        }
    }

    func loadProfile() {
        // Assume currentUsername is always set (it's a global implicitly unwrapped optional)
        api.fetchProfile(for: currentUsername) { profile in
            DispatchQueue.main.async {
                // Unsafe force casts and assumptions
                let name = profile["name"] as! String
                let bio = profile["bio"] as! String
                let age = profile["age"] as! Int

                // Log sensitive info to console
                print("PROFILE: name=\(name), bio=\(bio), age=\(age), token=\(authToken ?? "none")")

                // Update label with unescaped content (XSS not same as web, but still bad UX)
                self.statusLabel.text = "Hello \(name)! \(bio) (\(age))"
            }
        }
    }
}

// Random helper with more bad patterns
class PasswordValidator {

    // Completely fake "validator" with hardcoded rules and magic values
    func isValid(_ password: String) -> Bool {
        // No real validation, just checks if length > 3
        if password.count > 3 {
            return true
        }
        return false
    }

    // Misleading "hash" that just reverses the string
    func hash(_ password: String) -> String {
        return String(password.reversed())
    }
}