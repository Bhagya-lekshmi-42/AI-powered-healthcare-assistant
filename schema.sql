-- The app creates and upgrades this table automatically on first use.
-- You can also run this file manually: mysql -u root -p < schema.sql

CREATE DATABASE IF NOT EXISTS healthcare_db;
USE healthcare_db;

CREATE TABLE IF NOT EXISTS patients (
    id          INT AUTO_INCREMENT PRIMARY KEY,
    name        VARCHAR(100) NOT NULL,
    age         INT NOT NULL,
    symptoms    TEXT NOT NULL,
    ai_analysis TEXT NULL,
    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
