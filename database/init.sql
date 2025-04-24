CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    full_name TEXT NOT NULL,
    age INTEGER,
    dob TEXT,
    course TEXT,
    year TEXT,
    email TEXT UNIQUE,
    university TEXT,
    username TEXT UNIQUE,
    password TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS testimonies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    full_name TEXT,
    company TEXT,
    company_email TEXT,
    university TEXT,
    start_date TEXT,
    end_date TEXT,
    department TEXT,
    rating INTEGER,
    notes TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (username) REFERENCES users(username)
);

CREATE TABLE IF NOT EXISTS logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT,
    action TEXT,
    details TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);