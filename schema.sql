DROP TABLE IF EXISTS users;
DROP TABLE IF EXISTS salary;
DROP TABLE IF EXISTS attendance;
DROP TABLE IF EXISTS leave_requests;
DROP TABLE IF EXISTS skills;
DROP TABLE IF EXISTS certifications;

CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    employee_id TEXT UNIQUE NOT NULL,
    name TEXT NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    role TEXT NOT NULL DEFAULT 'employee',
    company TEXT DEFAULT 'Dayflow Inc',
    department TEXT DEFAULT '',
    designation TEXT DEFAULT '',
    manager TEXT DEFAULT '',
    location TEXT DEFAULT '',
    mobile TEXT DEFAULT '',
    dob TEXT DEFAULT '',
    address TEXT DEFAULT '',
    nationality TEXT DEFAULT '',
    personal_email TEXT DEFAULT '',
    gender TEXT DEFAULT '',
    marital_status TEXT DEFAULT '',
    date_of_joining TEXT DEFAULT '',
    bank_account TEXT DEFAULT '',
    bank_name TEXT DEFAULT '',
    ifsc_code TEXT DEFAULT '',
    pan_no TEXT DEFAULT '',
    uan_no TEXT DEFAULT '',
    about TEXT DEFAULT '',
    job_love TEXT DEFAULT '',
    hobbies TEXT DEFAULT ''
);

CREATE TABLE skills (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    skill_name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE certifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    certification_name TEXT NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE salary (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER UNIQUE NOT NULL,
    monthly_wage REAL NOT NULL DEFAULT 0,
    pf_rate REAL NOT NULL DEFAULT 12,
    professional_tax REAL NOT NULL DEFAULT 200,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE attendance (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    date TEXT NOT NULL,
    check_in TEXT DEFAULT '',
    check_out TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Present',
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE leave_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    leave_type TEXT NOT NULL,
    start_date TEXT NOT NULL,
    end_date TEXT NOT NULL,
    remarks TEXT DEFAULT '',
    status TEXT NOT NULL DEFAULT 'Pending',
    admin_comment TEXT DEFAULT '',
    FOREIGN KEY (user_id) REFERENCES users (id)
);