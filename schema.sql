-- create database and tables
CREATE DATABASE IF NOT EXISTS country_cache CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE country_cache;

CREATE TABLE IF NOT EXISTS countries (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    name_normalized VARCHAR(255) NOT NULL, -- lowercase for case-insensitive matching
    capital VARCHAR(255),
    region VARCHAR(100),
    population BIGINT NOT NULL,
    currency_code VARCHAR(10),
    exchange_rate DOUBLE,
    estimated_gdp DOUBLE,
    flag_url VARCHAR(500),
    last_refreshed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE KEY uq_name_normalized (name_normalized)
);

CREATE TABLE IF NOT EXISTS meta (
    key_name VARCHAR(100) PRIMARY KEY,
    value_text TEXT,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);

-- optional index to speed up region/currency queries
CREATE INDEX idx_region ON countries(region);
CREATE INDEX idx_currency ON countries(currency_code);
