-- =====================================================
-- COMPLETE SETUP: All tables for Queue Management System
-- Adapted for app.py (pin_code instead of password_hash)
-- =====================================================

-- ── OFFICES ──
CREATE TABLE IF NOT EXISTS offices (
    id INT AUTO_INCREMENT PRIMARY KEY,
    office_code VARCHAR(20) NOT NULL UNIQUE,
    office_number VARCHAR(20) DEFAULT NULL,
    office_name VARCHAR(100) NOT NULL,
    description TEXT DEFAULT NULL,
    location VARCHAR(100) DEFAULT NULL,
    is_active TINYINT(1) DEFAULT 1,
    display_order INT DEFAULT 0,
    availability_status VARCHAR(20) DEFAULT 'available',
    unavailability_notice TEXT DEFAULT NULL,
    availability_updated_at TIMESTAMP NULL DEFAULT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- ── OFFICERS ──
CREATE TABLE IF NOT EXISTS officers (
    id INT AUTO_INCREMENT PRIMARY KEY,
    officer_number INT NOT NULL UNIQUE,
    officer_name VARCHAR(100) NOT NULL,
    email VARCHAR(100),
    phone VARCHAR(20),
    pin_code VARCHAR(20) NOT NULL DEFAULT '1234',
    office_id INT NOT NULL,
    status ENUM('available','calling','serving','offline') DEFAULT 'available',
    status_reason TEXT DEFAULT NULL,
    desk_status ENUM('open','closed') DEFAULT 'open',
    current_token VARCHAR(20) DEFAULT NULL,
    is_admin TINYINT(1) DEFAULT 0,
    last_activity TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_officer_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE
);

-- ── SERVICES ──
CREATE TABLE IF NOT EXISTS services (
    id INT AUTO_INCREMENT PRIMARY KEY,
    service_code VARCHAR(20) NOT NULL,
    service_name VARCHAR(100) NOT NULL,
    office_id INT NOT NULL,
    description TEXT,
    estimated_time_minutes INT DEFAULT 5,
    is_active TINYINT(1) DEFAULT 1,
    display_order INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_service_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE,
    CONSTRAINT unique_service_per_office UNIQUE (office_id, service_code)
);

-- ── UNIVERSITY TOKENS ──
CREATE TABLE IF NOT EXISTS university_tokens (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_number VARCHAR(20) NOT NULL UNIQUE,
    office_id INT NOT NULL,
    service_id INT NOT NULL,
    service_code VARCHAR(20) NOT NULL,
    student_name VARCHAR(100),
    student_id VARCHAR(50),
    student_phone VARCHAR(20),
    parent_name VARCHAR(100),
    parent_phone VARCHAR(20),
    is_priority TINYINT(1) DEFAULT 0,
    status ENUM('waiting','called','serving','completed','skipped','cancelled','expired') DEFAULT 'waiting',
    requested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    called_at TIMESTAMP NULL DEFAULT NULL,
    serving_started_at TIMESTAMP NULL DEFAULT NULL,
    completed_at TIMESTAMP NULL DEFAULT NULL,
    skipped_at TIMESTAMP NULL DEFAULT NULL,
    assigned_officer_id INT DEFAULT NULL,
    assigned_officer_number INT DEFAULT NULL,
    queue_position INT DEFAULT NULL,
    estimated_wait_minutes INT DEFAULT NULL,
    source ENUM('kiosk','online','admin') DEFAULT 'kiosk',
    call_attempts INT DEFAULT 0,
    wait_duration_minutes INT DEFAULT NULL,
    service_duration_minutes INT DEFAULT NULL,
    rating TINYINT DEFAULT NULL,
    feedback_text TEXT DEFAULT NULL,
    feedback_submitted_at TIMESTAMP NULL DEFAULT NULL,
    CONSTRAINT fk_token_office FOREIGN KEY (office_id) REFERENCES offices(id),
    CONSTRAINT fk_token_service FOREIGN KEY (service_id) REFERENCES services(id),
    CONSTRAINT fk_token_officer FOREIGN KEY (assigned_officer_id) REFERENCES officers(id) ON DELETE SET NULL
);

-- ── OFFICE MESSAGES ──
CREATE TABLE IF NOT EXISTS office_messages (
    id INT AUTO_INCREMENT PRIMARY KEY,
    office_id INT NOT NULL,
    officer_id INT DEFAULT NULL,
    message TEXT NOT NULL,
    message_type ENUM('info','warning','success','error') DEFAULT 'info',
    is_active TINYINT(1) DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_message_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE,
    CONSTRAINT fk_message_officer FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE SET NULL
);

-- ── QUEUE LOGS ──
CREATE TABLE IF NOT EXISTS queue_logs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    token_number VARCHAR(20) NOT NULL,
    officer_id INT DEFAULT NULL,
    action VARCHAR(50) NOT NULL,
    action_details TEXT,
    old_status VARCHAR(20),
    new_status VARCHAR(20),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    INDEX idx_logs_action_created (action, created_at),
    CONSTRAINT fk_log_officer FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE SET NULL
);

-- ── QUEUE COUNTERS ──
CREATE TABLE IF NOT EXISTS queue_counters (
    office_id INT PRIMARY KEY,
    last_number INT DEFAULT 0,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    CONSTRAINT fk_counter_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE
);

-- ── OFFICER SESSIONS ──
CREATE TABLE IF NOT EXISTS officer_sessions (
    id INT AUTO_INCREMENT PRIMARY KEY,
    officer_id INT NOT NULL,
    office_id INT NOT NULL,
    session_date DATE NOT NULL,
    login_time DATETIME NOT NULL,
    logout_time DATETIME NULL,
    login_ip VARCHAR(45) NULL,
    login_location VARCHAR(255) DEFAULT NULL,
    logout_ip VARCHAR(45) NULL,
    device_info VARCHAR(255) NULL,
    status VARCHAR(20) DEFAULT 'active',
    tokens_served INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_session_officer FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE,
    CONSTRAINT fk_session_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE
);

-- ── OFFICER STATUS LOG ──
CREATE TABLE IF NOT EXISTS officer_status_log (
    id INT AUTO_INCREMENT PRIMARY KEY,
    session_id INT NOT NULL,
    officer_id INT NOT NULL,
    status VARCHAR(20) NOT NULL,
    started_at DATETIME NOT NULL,
    ended_at DATETIME NULL,
    duration_minutes INT DEFAULT 0,
    CONSTRAINT fk_statuslog_session FOREIGN KEY (session_id) REFERENCES officer_sessions(id) ON DELETE CASCADE,
    CONSTRAINT fk_statuslog_officer FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE
);

-- =====================================================
-- INDEXES
-- =====================================================
CREATE INDEX IF NOT EXISTS idx_officers_office ON officers(office_id);
CREATE INDEX IF NOT EXISTS idx_officers_status ON officers(status);
CREATE INDEX IF NOT EXISTS idx_officers_desk_status ON officers(desk_status);
CREATE INDEX IF NOT EXISTS idx_services_office ON services(office_id);
CREATE INDEX IF NOT EXISTS idx_tokens_office_status ON university_tokens(office_id, status);
CREATE INDEX IF NOT EXISTS idx_tokens_requested ON university_tokens(requested_at);
CREATE INDEX IF NOT EXISTS idx_tokens_service ON university_tokens(service_id);
CREATE INDEX IF NOT EXISTS idx_tokens_student_id ON university_tokens(student_id);
CREATE INDEX IF NOT EXISTS idx_tokens_student_unrated ON university_tokens(student_id, status, feedback_submitted_at);
CREATE INDEX IF NOT EXISTS idx_tokens_assigned_officer ON university_tokens(assigned_officer_id);
CREATE INDEX IF NOT EXISTS idx_tokens_feedback_submitted ON university_tokens(feedback_submitted_at);
CREATE INDEX IF NOT EXISTS idx_tokens_called ON university_tokens(called_at);
CREATE INDEX IF NOT EXISTS idx_tokens_serving ON university_tokens(serving_started_at);
CREATE INDEX IF NOT EXISTS idx_tokens_completed ON university_tokens(completed_at);
CREATE INDEX IF NOT EXISTS idx_tokens_skipped ON university_tokens(skipped_at);
CREATE INDEX IF NOT EXISTS idx_tokens_priority ON university_tokens(is_priority, office_id, status);
CREATE INDEX IF NOT EXISTS idx_logs_token ON queue_logs(token_number);
CREATE INDEX IF NOT EXISTS idx_logs_officer ON queue_logs(officer_id);
CREATE INDEX IF NOT EXISTS idx_offices_availability ON offices(availability_status);
CREATE INDEX IF NOT EXISTS idx_sessions_date ON officer_sessions(session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_officer_date ON officer_sessions(officer_id, session_date);
CREATE INDEX IF NOT EXISTS idx_sessions_status ON officer_sessions(status);
CREATE INDEX IF NOT EXISTS idx_statuslog_session ON officer_status_log(session_id);
CREATE INDEX IF NOT EXISTS idx_statuslog_officer ON officer_status_log(officer_id);
CREATE INDEX IF NOT EXISTS idx_statuslog_started ON officer_status_log(started_at);

-- =====================================================
-- SEED: OFFICES
-- =====================================================
INSERT IGNORE INTO offices (id, office_code, office_name, description, location, display_order) VALUES
(1, 'AR', 'Academic Registrar Office', 'Handles registry services', 'Main Building Floor 3', 1),
(2, 'REC', 'Records Office', 'Handles student records', 'Main Building Floor 1', 2),
(3, 'GC', 'Guidance and Counselling', 'Student counselling services', 'COCIS Block A', 3);

-- =====================================================
-- SEED: SERVICES
-- =====================================================
INSERT IGNORE INTO services (service_code, service_name, office_id, description, estimated_time_minutes, display_order) VALUES
('REG', 'Registry Services', 1, 'General registry inquiries', 5, 1),
('TST', 'Testimonial Letters', 1, 'Request testimonials', 10, 2),
('GEN', 'General Inquiry', 1, 'Other academic matters', 5, 3),
('ADM', 'Admission Letters', 2, 'Admission support', 5, 1),
('TRN', 'Transcript Issuance', 2, 'Official transcripts', 20, 2),
('YRO', 'Year One Registration', 2, 'First year registration', 10, 3),
('COU', 'Counselling Session', 3, 'Student counselling', 30, 1);

-- =====================================================
-- SEED: OFFICERS (with PIN codes for app.py)
-- =====================================================
INSERT IGNORE INTO officers (officer_number, officer_name, email, phone, pin_code, office_id, is_admin, status) VALUES
(101, 'Dr. Sarah Mukasa', 'sarah@university.ac.ug', '0700000101', '1234', 1, 0, 'available'),
(102, 'Mr. James Okello', 'james@university.ac.ug', '0700000102', '1234', 1, 0, 'available'),
(201, 'Ms. Grace Nambi', 'grace@university.ac.ug', '0700000201', '1234', 2, 0, 'available'),
(202, 'Mr. Peter Ssempijja', 'peter@university.ac.ug', '0700000202', '1234', 2, 0, 'available'),
(301, 'Ms. Alice Nakato', 'alice@university.ac.ug', '0700000301', '1234', 3, 0, 'available'),
(999, 'System Administrator', 'admin@university.ac.ug', '0700000999', 'admin1', 1, 1, 'available');

-- =====================================================
-- SEED: QUEUE COUNTERS
-- =====================================================
INSERT IGNORE INTO queue_counters (office_id, last_number) VALUES
(1, 0),
(2, 0),
(3, 0);
