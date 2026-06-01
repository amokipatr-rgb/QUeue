-- =====================================================
-- UNIVERSITY QUEUE MANAGEMENT SYSTEM DATABASE
-- Improved Production Version
-- =====================================================

CREATE DATABASE IF NOT EXISTS db;
USE db;

-- =====================================================
-- OFFICES TABLE
-- =====================================================

CREATE TABLE offices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    office_code VARCHAR(20) NOT NULL UNIQUE,
    office_number VARCHAR(20) DEFAULT NULL,
    
    office_name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    location VARCHAR(100) DEFAULT NULL,
    
    is_active TINYINT(1) DEFAULT 1,
    display_order INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- =====================================================
-- OFFICERS TABLE
-- =====================================================

CREATE TABLE officers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    officer_number INT NOT NULL UNIQUE,
    officer_name VARCHAR(100) NOT NULL,
    
    email VARCHAR(100) UNIQUE,
    phone VARCHAR(20),
    
    password_hash VARCHAR(255) NOT NULL,
    
    office_id INT NOT NULL,
    
    status ENUM(
        'available',
        'calling',
        'serving',
        'offline'
    ) DEFAULT 'available',
    
    current_token VARCHAR(20) DEFAULT NULL,
    
    is_admin TINYINT(1) DEFAULT 0,
    
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_officer_office
        FOREIGN KEY (office_id)
        REFERENCES offices(id)
        ON DELETE CASCADE
);

-- =====================================================
-- SERVICES TABLE
-- =====================================================

CREATE TABLE services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    
    service_code VARCHAR(20) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    
    office_id INT NOT NULL,
    
    description TEXT,
    
    estimated_time_minutes INT DEFAULT 5,
    
    is_active TINYINT(1) DEFAULT 1,
    display_order INT DEFAULT 0,
    
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_service_office
        FOREIGN KEY (office_id)
        REFERENCES offices(id)
        ON DELETE CASCADE,

    CONSTRAINT unique_service_per_office
        UNIQUE (office_id, service_code)
);

-- =====================================================
-- UNIVERSITY TOKENS TABLE
-- =====================================================

CREATE TABLE university_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,

    token_number VARCHAR(20) NOT NULL UNIQUE,

    office_id INT NOT NULL,
    service_id INT NOT NULL,

    service_code VARCHAR(20) NOT NULL,

    student_name VARCHAR(100),
    student_id VARCHAR(50),
    student_phone VARCHAR(20),

    status ENUM(
        'waiting',
        'called',
        'serving',
        'completed',
        'skipped',
        'cancelled',
        'expired'
    ) DEFAULT 'waiting',

    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    called_at TIMESTAMP NULL DEFAULT NULL,
    serving_started_at TIMESTAMP NULL DEFAULT NULL,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    skipped_at TIMESTAMP NULL DEFAULT NULL,

    assigned_officer_id INT DEFAULT NULL,
    assigned_officer_number INT DEFAULT NULL,

    queue_position INT DEFAULT NULL,
    estimated_wait_minutes INT DEFAULT NULL,

    source ENUM(
        'kiosk',
        'online',
        'admin'
    ) DEFAULT 'kiosk',

    call_attempts INT DEFAULT 0,

    wait_duration_minutes INT DEFAULT NULL,
    service_duration_minutes INT DEFAULT NULL,

    CONSTRAINT fk_token_office
        FOREIGN KEY (office_id)
        REFERENCES offices(id),

    CONSTRAINT fk_token_service
        FOREIGN KEY (service_id)
        REFERENCES services(id),

    CONSTRAINT fk_token_officer
        FOREIGN KEY (assigned_officer_id)
        REFERENCES officers(id)
        ON DELETE SET NULL
);

-- =====================================================
-- OFFICE MESSAGES TABLE
-- =====================================================

CREATE TABLE office_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,

    office_id INT NOT NULL,
    officer_id INT DEFAULT NULL,

    message TEXT NOT NULL,

    message_type ENUM(
        'info',
        'warning',
        'success',
        'error'
    ) DEFAULT 'info',

    is_active TINYINT(1) DEFAULT 1,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_message_office
        FOREIGN KEY (office_id)
        REFERENCES offices(id)
        ON DELETE CASCADE,

    CONSTRAINT fk_message_officer
        FOREIGN KEY (officer_id)
        REFERENCES officers(id)
        ON DELETE SET NULL
);

-- =====================================================
-- QUEUE LOGS TABLE
-- =====================================================

CREATE TABLE queue_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,

    token_number VARCHAR(20) NOT NULL,

    officer_id INT DEFAULT NULL,

    action VARCHAR(50) NOT NULL,
    action_details TEXT,

    old_status VARCHAR(20),
    new_status VARCHAR(20),

    ip_address VARCHAR(45),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_log_officer
        FOREIGN KEY (officer_id)
        REFERENCES officers(id)
        ON DELETE SET NULL
);

-- =====================================================
-- QUEUE COUNTERS TABLE
-- =====================================================

CREATE TABLE queue_counters (
    office_id INT PRIMARY KEY,

    last_number INT DEFAULT 0,

    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        ON UPDATE CURRENT_TIMESTAMP,

    CONSTRAINT fk_counter_office
        FOREIGN KEY (office_id)
        REFERENCES offices(id)
        ON DELETE CASCADE
);

-- =====================================================
-- INDEXES
-- =====================================================

CREATE INDEX idx_officers_office
ON officers(office_id);

CREATE INDEX idx_services_office
ON services(office_id);

CREATE INDEX idx_tokens_office_status
ON university_tokens(office_id, status);

CREATE INDEX idx_tokens_requested
ON university_tokens(requested_at);

CREATE INDEX idx_tokens_service
ON university_tokens(service_id);

CREATE INDEX idx_tokens_phone
ON university_tokens(student_phone);

CREATE INDEX idx_logs_token
ON queue_logs(token_number);

CREATE INDEX idx_logs_action
ON queue_logs(action);

-- =====================================================
-- SAMPLE OFFICES
-- =====================================================

INSERT INTO offices (
    office_code,
    office_name,
    description,
    location,
    display_order
)
VALUES
(
    'AR',
    'Academic Registrar Office',
    'Handles registry services',
    'Main Building Floor 3',
    1
),
(
    'REC',
    'Records Office',
    'Handles student records',
    'Main Building Floor 1',
    2
),
(
    'GC',
    'Guidance and Counselling',
    'Student counselling services',
    'COCIS Block A',
    3
);

-- =====================================================
-- INITIAL QUEUE COUNTERS
-- =====================================================

INSERT INTO queue_counters (office_id, last_number)
VALUES
(1,0),
(2,0),
(3,0);

-- =====================================================
-- SAMPLE SERVICES
-- =====================================================

INSERT INTO services (
    service_code,
    service_name,
    office_id,
    description,
    estimated_time_minutes,
    display_order
)
VALUES
(
    'REG',
    'Registry Services',
    1,
    'General registry inquiries',
    5,
    1
),
(
    'TST',
    'Testimonial Letters',
    1,
    'Request testimonials',
    10,
    2
),
(
    'ADM',
    'Admission Letters',
    2,
    'Admission support',
    5,
    1
),
(
    'TRN',
    'Transcript Issuance',
    2,
    'Official transcripts',
    20,
    2
),
(
    'COU',
    'Counselling Session',
    3,
    'Student counselling',
    30,
    1
);

-- =====================================================
-- SAMPLE OFFICERS
-- PASSWORDS SHOULD BE HASHED IN PHP
-- =====================================================

INSERT INTO officers (
    officer_number,
    officer_name,
    email,
    password_hash,
    office_id,
    is_admin
)
VALUES
(
    101,
    'Dr. Sarah Mukasa',
    'sarah@university.ac.ug',
    '$2y$10$examplehash',
    1,
    0
),
(
    102,
    'Mr. James Okello',
    'james@university.ac.ug',
    '$2y$10$examplehash',
    1,
    0
),
(
    201,
    'Ms. Grace Nambi',
    'grace@university.ac.ug',
    '$2y$10$examplehash',
    2,
    0
),
(
    999,
    'System Administrator',
    'admin@university.ac.ug',
    '$2y$10$examplehash',
    1,
    1
);

-- =====================================================
-- GENERATE NEXT TOKEN QUERY
-- =====================================================

-- STEP 1:
-- Get current counter

SELECT last_number
FROM queue_counters
WHERE office_id = 1;

-- STEP 2:
-- Increase counter

UPDATE queue_counters
SET last_number = last_number + 1
WHERE office_id = 1;

-- STEP 3:
-- Generate token example in PHP:
-- AR0001
-- AR0002

-- =====================================================
-- INSERT NEW TOKEN
-- =====================================================

INSERT INTO university_tokens (
    token_number,
    office_id,
    service_id,
    service_code,
    student_name,
    student_phone,
    queue_position,
    estimated_wait_minutes
)
VALUES (
    'AR0001',
    1,
    1,
    'REG',
    'John Doe',
    '0700000000',
    1,
    5
);

-- =====================================================
-- GET WAITING TOKENS
-- =====================================================

SELECT
    t.*,
    s.service_name
FROM university_tokens t
JOIN services s
    ON t.service_id = s.id
WHERE t.office_id = 1
AND t.status = 'waiting'
ORDER BY t.requested_at ASC;

-- =====================================================
-- CALL NEXT TOKEN
-- =====================================================

UPDATE university_tokens
SET
    status = 'called',
    called_at = NOW(),
    assigned_officer_id = 1,
    assigned_officer_number = 101
WHERE id = 1;

-- =====================================================
-- START SERVING TOKEN
-- =====================================================

UPDATE university_tokens
SET
    status = 'serving',
    serving_started_at = NOW()
WHERE id = 1;

-- =====================================================
-- COMPLETE TOKEN
-- =====================================================

UPDATE university_tokens
SET
    status = 'completed',
    completed_at = NOW(),
    service_duration_minutes =
        TIMESTAMPDIFF(
            MINUTE,
            serving_started_at,
            NOW()
        )
WHERE id = 1;

-- =====================================================
-- SKIP TOKEN
-- =====================================================

UPDATE university_tokens
SET
    status = 'skipped',
    skipped_at = NOW()
WHERE id = 1;

-- =====================================================
-- OFFICER STATUS UPDATE
-- =====================================================

UPDATE officers
SET
    status = 'serving',
    current_token = 'AR0001'
WHERE id = 1;

-- =====================================================
-- INSERT QUEUE LOG
-- =====================================================

INSERT INTO queue_logs (
    token_number,
    officer_id,
    action,
    action_details,
    old_status,
    new_status,
    ip_address
)
VALUES (
    'AR0001',
    1,
    'call_token',
    'Called from dashboard',
    'waiting',
    'called',
    '127.0.0.1'
);

-- =====================================================
-- DASHBOARD STATISTICS
-- =====================================================

SELECT
    COUNT(*) AS total_tokens,
    
    SUM(status='waiting') AS waiting,
    SUM(status='called') AS called,
    SUM(status='serving') AS serving,
    SUM(status='completed') AS completed
    
FROM university_tokens;

-- =====================================================
-- CURRENT SERVING TOKENS
-- =====================================================

SELECT
    t.token_number,
    t.student_name,
    o.officer_name,
    ofc.office_name
FROM university_tokens t
JOIN officers o
    ON t.assigned_officer_id = o.id
JOIN offices ofc
    ON t.office_id = ofc.id
WHERE t.status = 'serving';

-- =====================================================
-- TODAY REPORT
-- =====================================================

SELECT
    office_id,
    COUNT(*) AS total_served
FROM university_tokens
WHERE DATE(completed_at) = CURDATE()
GROUP BY office_id;

-- =====================================================
-- AVERAGE WAIT TIME
-- =====================================================

SELECT
    AVG(
        TIMESTAMPDIFF(
            MINUTE,
            requested_at,
            called_at
        )
    ) AS avg_wait_minutes
FROM university_tokens
WHERE called_at IS NOT NULL;

-- =====================================================
-- RESET QUEUE
-- =====================================================

UPDATE queue_counters
SET last_number = 0
WHERE office_id = 1;

-- =====================================================
-- END
-- =====================================================