"""
Complete database setup: creates all tables, seeds data, creates admin.
Run: python migrations/setup_database.py
"""
import mysql.connector

conn = mysql.connector.connect(host='127.0.0.1', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

def table_exists(name):
    cursor.execute("SHOW TABLES LIKE %s", (name,))
    return cursor.fetchone() is not None

def column_exists(table, col):
    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE %s", (col,))
    return cursor.fetchone() is not None

def index_exists(table, idx):
    cursor.execute(f"SHOW INDEX FROM {table} WHERE Key_name = %s", (idx,))
    return cursor.fetchone() is not None

def create_index_if_missing(name, table, col):
    if not index_exists(table, name):
        cursor.execute(f"CREATE INDEX {name} ON {table}({col})")
        print(f"  [OK] Created index {name}")

# ── OFFICES ──
if not table_exists('offices'):
    cursor.execute("""
        CREATE TABLE offices (
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
        )
    """)
    print("[OK] Created offices table")
else:
    print("[OK] offices table exists")
    if not column_exists('offices', 'availability_status'):
        cursor.execute("ALTER TABLE offices ADD COLUMN availability_status VARCHAR(20) DEFAULT 'available'")
        print("  [OK] Added availability_status to offices")
    if not column_exists('offices', 'unavailability_notice'):
        cursor.execute("ALTER TABLE offices ADD COLUMN unavailability_notice TEXT DEFAULT NULL AFTER availability_status")
        print("  [OK] Added unavailability_notice to offices")
    if not column_exists('offices', 'availability_updated_at'):
        cursor.execute("ALTER TABLE offices ADD COLUMN availability_updated_at TIMESTAMP NULL DEFAULT NULL AFTER unavailability_notice")
        print("  [OK] Added availability_updated_at to offices")

# ── OFFICERS ──
if not table_exists('officers'):
    cursor.execute("""
        CREATE TABLE officers (
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
        )
    """)
    print("[OK] Created officers table")
else:
    print("[OK] officers table exists")
    for col, definition in [
        ('pin_code', "ALTER TABLE officers ADD COLUMN pin_code VARCHAR(20) DEFAULT '1234'"),
        ('status_reason', "ALTER TABLE officers ADD COLUMN status_reason TEXT DEFAULT NULL"),
        ('desk_status', "ALTER TABLE officers ADD COLUMN desk_status ENUM('open','closed') DEFAULT 'open'"),
    ]:
        if not column_exists('officers', col):
            cursor.execute(definition)
            print(f"  [OK] Added column {col} to officers")

# ── SERVICES ──
if not table_exists('services'):
    cursor.execute("""
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
            CONSTRAINT fk_service_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE,
            CONSTRAINT unique_service_per_office UNIQUE (office_id, service_code)
        )
    """)
    print("[OK] Created services table")
else:
    print("[OK] services table exists")

# ── UNIVERSITY TOKENS ──
if not table_exists('university_tokens'):
    cursor.execute("""
        CREATE TABLE university_tokens (
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
        )
    """)
    print("[OK] Created university_tokens table")
else:
    print("[OK] university_tokens table exists")
    # Migration: add missing columns
    for col, definition in [
        ('rating', "ALTER TABLE university_tokens ADD COLUMN rating TINYINT DEFAULT NULL"),
        ('feedback_text', "ALTER TABLE university_tokens ADD COLUMN feedback_text TEXT DEFAULT NULL"),
        ('feedback_submitted_at', "ALTER TABLE university_tokens ADD COLUMN feedback_submitted_at TIMESTAMP NULL DEFAULT NULL"),
        ('parent_name', "ALTER TABLE university_tokens ADD COLUMN parent_name VARCHAR(100) DEFAULT NULL"),
        ('parent_phone', "ALTER TABLE university_tokens ADD COLUMN parent_phone VARCHAR(20) DEFAULT NULL"),
        ('is_priority', "ALTER TABLE university_tokens ADD COLUMN is_priority TINYINT(1) DEFAULT 0"),
    ]:
        if not column_exists('university_tokens', col):
            cursor.execute(definition)
            print(f"  [OK] Added column {col} to university_tokens")

# ── OFFICE MESSAGES ──
if not table_exists('office_messages'):
    cursor.execute("""
        CREATE TABLE office_messages (
            id INT AUTO_INCREMENT PRIMARY KEY,
            office_id INT NOT NULL,
            officer_id INT DEFAULT NULL,
            message TEXT NOT NULL,
            message_type ENUM('info','warning','success','error') DEFAULT 'info',
            is_active TINYINT(1) DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT fk_message_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE,
            CONSTRAINT fk_message_officer FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE SET NULL
        )
    """)
    print("[OK] Created office_messages table")
else:
    print("[OK] office_messages table exists")

# ── QUEUE LOGS ──
if not table_exists('queue_logs'):
    cursor.execute("""
        CREATE TABLE queue_logs (
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
        )
    """)
    print("[OK] Created queue_logs table")
else:
    print("[OK] queue_logs table exists")

# ── QUEUE COUNTERS ──
if not table_exists('queue_counters'):
    cursor.execute("""
        CREATE TABLE queue_counters (
            office_id INT PRIMARY KEY,
            last_number INT DEFAULT 0,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
            CONSTRAINT fk_counter_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE
        )
    """)
    print("[OK] Created queue_counters table")
else:
    print("[OK] queue_counters table exists")

conn.commit()

# ── OFFICER SESSIONS ──
if not table_exists('officer_sessions'):
    cursor.execute("""
        CREATE TABLE officer_sessions (
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
        )
    """)
    print("[OK] Created officer_sessions table")
else:
    print("[OK] officer_sessions table exists")

# ── OFFICER STATUS LOG ──
if not table_exists('officer_status_log'):
    cursor.execute("""
        CREATE TABLE officer_status_log (
            id INT AUTO_INCREMENT PRIMARY KEY,
            session_id INT NOT NULL,
            officer_id INT NOT NULL,
            status VARCHAR(20) NOT NULL,
            started_at DATETIME NOT NULL,
            ended_at DATETIME NULL,
            duration_minutes INT DEFAULT 0,
            CONSTRAINT fk_statuslog_session FOREIGN KEY (session_id) REFERENCES officer_sessions(id) ON DELETE CASCADE,
            CONSTRAINT fk_statuslog_officer FOREIGN KEY (officer_id) REFERENCES officers(id) ON DELETE CASCADE
        )
    """)
    print("[OK] Created officer_status_log table")
else:
    print("[OK] officer_status_log table exists")


# ── GENERAL COMPLAINTS ──
if not table_exists('general_complaints'):
    cursor.execute("""
        CREATE TABLE general_complaints (
            id INT AUTO_INCREMENT PRIMARY KEY,
            category VARCHAR(20) NOT NULL,
            full_name VARCHAR(100) DEFAULT NULL,
            student_number VARCHAR(50) DEFAULT NULL,
            employee_id VARCHAR(50) DEFAULT NULL,
            department VARCHAR(100) DEFAULT NULL,
            contact VARCHAR(100) DEFAULT NULL,
            complaint_text TEXT NOT NULL,
            status VARCHAR(20) DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("[OK] Created general_complaints table")
else:
    print("[OK] general_complaints table exists")


# ── INDEXES ──
print("\n[INDEXES]")
for name, table, col in [
    ('idx_officers_office', 'officers', 'office_id'),
    ('idx_officers_status', 'officers', 'status'),
    ('idx_officers_desk_status', 'officers', 'desk_status'),
    ('idx_services_office', 'services', 'office_id'),
    ('idx_tokens_office_status', 'university_tokens', 'office_id, status'),
    ('idx_tokens_requested', 'university_tokens', 'requested_at'),
    ('idx_tokens_service', 'university_tokens', 'service_id'),
    ('idx_tokens_student_id', 'university_tokens', 'student_id'),
    ('idx_tokens_assigned_officer', 'university_tokens', 'assigned_officer_id'),
    ('idx_tokens_feedback_submitted', 'university_tokens', 'feedback_submitted_at'),
    ('idx_tokens_called', 'university_tokens', 'called_at'),
    ('idx_tokens_serving', 'university_tokens', 'serving_started_at'),
    ('idx_tokens_completed', 'university_tokens', 'completed_at'),
    ('idx_tokens_skipped', 'university_tokens', 'skipped_at'),
    ('idx_tokens_priority', 'university_tokens', 'is_priority, office_id, status'),
    ('idx_logs_token', 'queue_logs', 'token_number'),
    ('idx_logs_officer', 'queue_logs', 'officer_id'),
    ('idx_offices_availability', 'offices', 'availability_status'),
    ('idx_sessions_date', 'officer_sessions', 'session_date'),
    ('idx_sessions_officer_date', 'officer_sessions', 'officer_id, session_date'),
    ('idx_sessions_status', 'officer_sessions', 'status'),
    ('idx_statuslog_session', 'officer_status_log', 'session_id'),
    ('idx_statuslog_officer', 'officer_status_log', 'officer_id'),
    ('idx_statuslog_started', 'officer_status_log', 'started_at'),
]:
    create_index_if_missing(name, table, col)

# Check for student unrated index (special name)
if not index_exists('university_tokens', 'idx_tokens_student_unrated'):
    cursor.execute("CREATE INDEX idx_tokens_student_unrated ON university_tokens(student_id, status, feedback_submitted_at)")
    print("  [OK] Created index idx_tokens_student_unrated")

# ── FIX MISSING COLUMNS ON EXISTING TABLES ──
for table, col, definition in [
    ('officer_sessions', 'login_location', "ADD COLUMN login_location VARCHAR(255) DEFAULT NULL AFTER login_ip"),
    ('officer_sessions', 'logout_ip', "ADD COLUMN logout_ip VARCHAR(45) AFTER login_location"),
]:
    cursor.execute(f"SHOW COLUMNS FROM {table} LIKE '{col}'")
    if not cursor.fetchone():
        print(f"[WARN] {table} missing {col}! Adding...")
        cursor.execute(f"ALTER TABLE {table} {definition}")
        conn.commit()
        print(f"[OK] {col} added to {table}")

conn.commit()

# ── SEED DATA ──
print("\n[SEED]")

# Offices
cursor.execute("SELECT COUNT(*) FROM offices")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO offices (office_code, office_name, description, location, display_order) VALUES (%s, %s, %s, %s, %s)",
        [
            ('AR', 'Academic Registrar Office', 'Handles registry services', 'Main Building Floor 3', 1),
            ('REC', 'Records Office', 'Handles student records', 'Main Building Floor 1', 2),
            ('GC', 'Guidance and Counselling', 'Student counselling services', 'COCIS Block A', 3),
        ]
    )
    conn.commit()
    print("  [OK] Seeded 3 offices")
else:
    print("  [SKIP] Offices already seeded")

# Services
cursor.execute("SELECT COUNT(*) FROM services")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO services (service_code, service_name, office_id, description, estimated_time_minutes, display_order) VALUES (%s, %s, %s, %s, %s, %s)",
        [
            ('REG', 'Registry Services', 1, 'General registry inquiries', 5, 1),
            ('TST', 'Testimonial Letters', 1, 'Request testimonials', 10, 2),
            ('GEN', 'General Inquiry', 1, 'Other academic matters', 5, 3),
            ('ADM', 'Admission Letters', 2, 'Admission support', 5, 1),
            ('TRN', 'Transcript Issuance', 2, 'Official transcripts', 20, 2),
            ('YRO', 'Year One Registration', 2, 'First year registration', 10, 3),
            ('COU', 'Counselling Session', 3, 'Student counselling', 30, 1),
        ]
    )
    conn.commit()
    print("  [OK] Seeded 7 services")
else:
    print("  [SKIP] Services already seeded")

# Officers
cursor.execute("SELECT COUNT(*) FROM officers")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO officers (officer_number, officer_name, email, phone, pin_code, office_id, is_admin, status) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
        [
            (101, 'Dr. Sarah Mukasa', 'sarah@university.ac.ug', '0700000101', '1234', 1, 0, 'available'),
            (102, 'Mr. James Okello', 'james@university.ac.ug', '0700000102', '1234', 1, 0, 'available'),
            (201, 'Ms. Grace Nambi', 'grace@university.ac.ug', '0700000201', '1234', 2, 0, 'available'),
            (202, 'Mr. Peter Ssempijja', 'peter@university.ac.ug', '0700000202', '1234', 2, 0, 'available'),
            (301, 'Ms. Alice Nakato', 'alice@university.ac.ug', '0700000301', '1234', 3, 0, 'available'),
            (999, 'System Administrator', 'admin@university.ac.ug', '0700000999', 'admin1', 1, 1, 'available'),
        ]
    )
    conn.commit()
    print("  [OK] Seeded 6 officers (incl. admin)")
else:
    print("  [SKIP] Officers already seeded")

# Queue counters
cursor.execute("SELECT COUNT(*) FROM queue_counters")
if cursor.fetchone()[0] == 0:
    cursor.executemany(
        "INSERT INTO queue_counters (office_id, last_number) VALUES (%s, %s)",
        [(1, 0), (2, 0), (3, 0)]
    )
    conn.commit()
    print("  [OK] Seeded queue counters")
else:
    print("  [SKIP] Queue counters already seeded")

# ── ENSURE admin exists with known PIN ──
cursor.execute("SELECT id FROM officers WHERE is_admin = 1 AND pin_code = 'admin1'")
if not cursor.fetchone():
    cursor.execute("UPDATE officers SET pin_code = 'admin1' WHERE is_admin = 1")
    conn.commit()
    # If no admin exists, create one
    cursor.execute("SELECT id FROM officers WHERE is_admin = 1")
    if not cursor.fetchone():
        cursor.execute("""
            INSERT INTO officers (officer_number, officer_name, email, phone, pin_code, office_id, is_admin, status)
            VALUES (999, 'System Administrator', 'admin@university.ac.ug', '0700000999', 'admin1', 1, 1, 'available')
        """)
        conn.commit()
        print("  [OK] Created admin account")
print("  [OK] Admin PIN verified: admin1")

cursor.close()
conn.close()

print("\n" + "=" * 50)
print("DATABASE SETUP COMPLETE")
print("=" * 50)
print("\nAdmin login:")
print("  Officer Number: 999")
print("  PIN: admin1")
print("\nOfficer logins (all PIN: 1234):")
print("  #101 - Dr. Sarah Mukasa (AR)")
print("  #102 - Mr. James Okello (AR)")
print("  #201 - Ms. Grace Nambi (REC)")
print("  #202 - Mr. Peter Ssempijja (REC)")
print("  #301 - Ms. Alice Nakato (GC)")
