SET NAMES utf8mb4;
CREATE DATABASE IF NOT EXISTS mydatabase CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;
USE mydatabase;

CREATE TABLE users 
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    username VARCHAR(255) NOT NULL,
    sub VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    role ENUM('admin', 'user') DEFAULT 'user',
    image_url VARCHAR(255) DEFAULT 'https://via.placeholder.com/150'
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

CREATE TABLE posts 
(
    id INT AUTO_INCREMENT PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    user_id INT,
    username VARCHAR(255) NOT NULL,
    is_private BOOLEAN DEFAULT FALSE,
    FOREIGN KEY (user_id) REFERENCES users(id)
) CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci;

-- adminユーザーの追加, image_urlにBOLA_FLAG1を格納
INSERT INTO users (username, sub, hashed_password, role, image_url) VALUES ('admin', '9c3d153c-4951-4238-8a27-a0137469c2d4', '$2a$04$tW5NykUb1cGVtB.r/qtmBu07TWXVXdyrmdohizsgUBW5qWx7j8lma', 'admin', 'flag{dummy_flag}');
-- adminのprivateなpostの追加, contentにBOLA_FLAG2を格納
INSERT INTO posts (title, content, user_id, username, is_private) VALUES ('Welcome to admin private blog!', 'flag is flag{dummy_flag}', 1, 'admin', TRUE);

INSERT INTO users (username, sub, hashed_password, role) 
VALUES ('testuser', 'b2c3d4e5-f6g7-8901-hi23-jklmnopqrstuv', '$2a$04$5s7o.GoqcSl1GydjVVkkl.PJ8vgw3YCMTmYP0PjwNPbKt2qS4J21i', 'user');

INSERT INTO posts (title, content, user_id, username, is_private) 
VALUES 
('不思議な森の一日', '今日、私は不思議な森を見つけて、探検することにしました。', LAST_INSERT_ID(), 'testuser', FALSE),
('オススメのカフェ', '今日新しいカフェを訪れた。とても落ち着く雰囲気だった。', LAST_INSERT_ID(), 'testuser', FALSE),
('現代アートについての感想', '最近、現代アートの美術館を訪れた。いくつかの作品は難解だったが、他は魅力的だった。', LAST_INSERT_ID(), 'testuser', FALSE),
('山へのハイキング', '先週末、美しい山にハイキングに行った。頂上からの眺めは息をのむようだった！', LAST_INSERT_ID(), 'testuser', FALSE),
('読書のおすすめ', '最近、すばらしい本を読んでいる。次に読むべきおすすめの本はありますか？', LAST_INSERT_ID(), 'testuser', FALSE);