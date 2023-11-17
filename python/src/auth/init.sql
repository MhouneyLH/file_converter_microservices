/* THIS IS LIKE A SQL SCRIPT */
/* user for the actual database */
CREATE USER 'auth_user'@'localhost' IDENTIFIED BY 'auth_user123';

CREATE DATABASE auth;

/* this user will have the rights to connect to the API-Gateway */
GRANT ALL PRIVILEGES ON auth.* TO 'auth_user'@'localhost';

/* use this database */
USE auth;

CREATE TABLE user (
    id INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
    email VARCHAR(255) NOT NULL UNIQUE,
    password VARCHAR(255) NOT NULL
);

INSERT INTO user(email, password) VALUES ('lucas@email.com', "Huhn123");