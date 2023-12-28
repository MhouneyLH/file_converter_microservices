/* user for the actual database */
-- CREATE USER 'auth_user'@'mp3converter.com' IDENTIFIED BY 'Auth123';
CREATE USER 'auth_user'@'%' IDENTIFIED BY 'Auth123';

CREATE DATABASE auth;

/* this user will have the rights to connect to the API-Gateway */
-- GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'mp3converter.com';
GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'%';
FLUSH PRIVILEGES;

/* use this database */
USE auth;

CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

/* With this data the user can authenticate */
INSERT INTO user(email, password) VALUES ('lucas.huenniger02@gmail.com', "Auth123");