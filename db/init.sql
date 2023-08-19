CREATE DATABASE IF NOT EXISTS mydatabase;
USE mydatabase;

CREATE TABLE users 
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    image_url VARCHAR(255)
);

CREATE TABLE posts 
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    user_id INT,
    is_private BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id)
)DEFAULT CHARACTER SET=utf8mb4;