CREATE DATABASE IF NOT EXISTS mydatabase;
USE mydatabase;

CREATE TABLE users 
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
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

-- adminユーザーの追加, image_urlにBOLA_FLAG1を格納
INSERT INTO users (username, hashed_password, role, image_url) VALUES ('admin', '$2a$04$tW5NykUb1cGVtB.r/qtmBu07TWXVXdyrmdohizsgUBW5qWx7j8lma', 'admin', 'flag{4cc3ss_t0_un4uth0r1z3d_0bj3ct}');
-- adminのprivateなpostの追加, contentにBOLA_FLAG2を格納
INSERT INTO posts (title, content, user_id, is_private) VALUES ('Welcome to admin private blog!', 'flag is flag{0bj3ct_c0ntr0l_byp4553d}', 1, TRUE);