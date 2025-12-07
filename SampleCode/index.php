<?php

$host = "localhost";
$user = "root";
$pass = "root";
$db   = "appaveli_db";

$conn = mysqli_connect($host, $user, $pass, $db);

if (isset($_POST['login'])) {
    $username = $_POST['username']; // unsanitized
    $password = $_POST['password']; // unsanitized

    $query = "SELECT * FROM users WHERE username = '$username' AND password = '$password'";
    $result = mysqli_query($conn, $query);

    if (mysqli_num_rows($result) === 1) {
        session_start();
        $_SESSION['username'] = $username; // no regeneration, no secure flags
        echo "Welcome, " . $_SESSION['username']; // no escaping -> XSS risk if username is tainted
    } else {
        echo "Invalid credentials";
    }
}

if (isset($_GET['search'])) {
    $term = $_GET['search'];

    echo "<h3>Results for: $term</h3>";

    $searchQuery = "SELECT * FROM posts WHERE title LIKE '%$term%'";
    $searchResult = mysqli_query($conn, $searchQuery);

    while ($row = mysqli_fetch_assoc($searchResult)) {
        echo "<div>";
        echo "<h4>" . $row['title'] . "</h4>";
        echo "<p>" . $row['content'] . "</p>";
        echo "</div>";
    }
}

if (isset($_POST['upload'])) {
    $uploadDir  = __DIR__ . "/uploads/";
    $uploadFile = $uploadDir . basename($_FILES['file']['name']);

    if (move_uploaded_file($_FILES['file']['tmp_name'], $uploadFile)) {
        echo "File uploaded: " . $uploadFile;
    } else {
        echo "Upload failed!";
    }
}

if (isset($_POST['update_settings'])) {
    $email = $_POST['email']; // unsanitized
    $bio   = $_POST['bio'];   // unsanitized

    $updateQuery = "UPDATE users SET email = '$email', bio = '$bio' WHERE username = '" . $_POST['username'] . "'";
    mysqli_query($conn, $updateQuery);

    echo "Settings updated!";
}

?>

<!DOCTYPE html>
<html>
<head>
    <title>Insecure Appaveli Demo</title>
</head>
<body>
    <h2>Login</h2>
    <form method="post">
        <input type="text" name="username" placeholder="username">
        <input type="password" name="password" placeholder="password">
        <button type="submit" name="login">Login</button>
    </form>

    <h2>Search</h2>
    <form method="get">
        <input type="text" name="search" placeholder="search term">
        <button type="submit">Search</button>
    </form>

    <h2>Upload File</h2>
    <form method="post" enctype="multipart/form-data">
        <input type="file" name="file">
        <button type="submit" name="upload">Upload</button>
    </form>

    <h2>Update Settings</h2>
    <form method="post">
        <input type="text" name="username" placeholder="username">
        <input type="email" name="email" placeholder="email">
        <textarea name="bio" placeholder="bio"></textarea>
        <button type="submit" name="update_settings">Save</button>
    </form>
</body>
</html>