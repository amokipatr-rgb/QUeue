from flask import Flask, request, jsonify, send_from_directory, redirect
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
from calendar import monthrange
import logging
import secrets
import os
import re
import smtplib
from email.message import EmailMessage
import traceback
import asyncio
import time
import urllib.request
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ── SMTP (set via env so never in git) ──
SMTP_HOST = 'smtp.gmail.com'
SMTP_PORT = 587
SMTP_USER = os.environ.get('MAIL_USERNAME', '')
SMTP_PASS = os.environ.get('MAIL_PASSWORD', '')
SMTP_FROM = SMTP_USER  # same as username for Gmail

def geoip(ip):
    """Resolve an IP address to a location string using ip-api.com (free, no key)."""
    if ip.startswith(('127.', '192.168.', '10.', '172.')):
        return 'Local Network'
    try:
        url = f'http://ip-api.com/json/{ip}?fields=status,city,regionName,country,lat,lon,zip,isp,org&lang=en'
        with urllib.request.urlopen(url, timeout=3) as r:
            d = json.loads(r.read())
            if d.get('status') == 'success':
                parts = [d.get('city',''), d.get('regionName',''), d.get('country','')]
                loc = ', '.join(p for p in parts if p)
                if d.get('lat') and d.get('lon'):
                    loc += f' ({d["lat"]}, {d["lon"]})'
                return loc
    except:
        pass
    return ip

app = Flask(__name__)
CORS(app)

# ============================================
# DATABASE CONFIGURATION
# ============================================
def _build_db_config():
    _url = os.environ.get('MYSQL_URL') or os.environ.get('DATABASE_URL')
    if _url:
        m = re.match(r'mysql://([^:]+):([^@]*)@([^:]+):(\d+)/(.+)', _url)
        if m:
            return {
                'host': m.group(3), 'port': int(m.group(4)),
                'user': m.group(1), 'password': m.group(2),
                'database': m.group(5)
            }, f"MYSQL_URL ({m.group(3)}:{m.group(4)})"
        print("[WARN] Could not parse MYSQL_URL, trying individual vars")

    host = os.environ.get('MYSQLHOST') or os.environ.get('MYSQL_HOST')
    if host:
        return {
            'host': host,
            'port': int(os.environ.get('MYSQLPORT') or os.environ.get('MYSQL_PORT') or 3306),
            'user': os.environ.get('MYSQLUSER') or os.environ.get('MYSQL_USER') or 'root',
            'password': os.environ.get('MYSQLPASSWORD') or os.environ.get('MYSQL_PASSWORD') or '',
            'database': os.environ.get('MYSQLDATABASE') or os.environ.get('MYSQL_DATABASE') or 'railway'
        }, f"individual MYSQL_* vars ({host})"
    return None, None

DB_CONFIG, _src = _build_db_config()
if not DB_CONFIG:
    raise RuntimeError("No database configuration found. Set MYSQL_URL or MYSQLHOST/MYSQL_PORT/etc.")
print(f"[OK] DB config from {_src}")

def _ensure_indexes(cursor, connection):
    required = [
        ('idx_logs_officer', 'queue_logs', 'officer_id'),
        ('idx_tokens_assigned_officer', 'university_tokens', 'assigned_officer_id'),
        ('idx_tokens_feedback_submitted', 'university_tokens', 'feedback_submitted_at'),
        ('idx_tokens_called', 'university_tokens', 'called_at'),
        ('idx_tokens_serving_started', 'university_tokens', 'serving_started_at'),
        ('idx_tokens_completed', 'university_tokens', 'completed_at'),
        ('idx_tokens_skipped', 'university_tokens', 'skipped_at'),
        ('idx_offices_availability', 'offices', 'availability_status'),
    ]
    for name, table, col in required:
        try:
            cursor.execute(f"CREATE INDEX {name} ON {table}({col})")
            connection.commit()
            print(f"[OK] Created index {name} on {table}({col})")
        except mysql.connector.Error as e:
            if "Duplicate key name" in str(e):
                pass  # already exists
            else:
                print(f"[WARN] Could not create index {name}: {e}")

# ── TABLE CREATION HELPERS ──
_CREATE_OFFICES_SQL = """
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
    )"""
_CREATE_OFFICERS_SQL = """
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
    )"""
_CREATE_SERVICES_SQL = """
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
    )"""
_CREATE_UNIVERSITY_TOKENS_SQL = """
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
    )"""
_CREATE_OFFICE_MESSAGES_SQL = """
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
    )"""
_CREATE_QUEUE_LOGS_SQL = """
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
    )"""
_CREATE_QUEUE_COUNTERS_SQL = """
    CREATE TABLE IF NOT EXISTS queue_counters (
        office_id INT PRIMARY KEY,
        last_number INT DEFAULT 0,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
        CONSTRAINT fk_counter_office FOREIGN KEY (office_id) REFERENCES offices(id) ON DELETE CASCADE
    )"""
_CREATE_OFFICER_SESSIONS_SQL = """
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
    )"""
_CREATE_OFFICER_STATUS_LOG_SQL = """
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
    )"""
_CREATE_GENERAL_COMPLAINTS_SQL = """
    CREATE TABLE IF NOT EXISTS general_complaints (
        id INT AUTO_INCREMENT PRIMARY KEY,
        category VARCHAR(20) NOT NULL,
        full_name VARCHAR(100) DEFAULT NULL,
        student_number VARCHAR(50) DEFAULT NULL,
        employee_id VARCHAR(50) DEFAULT NULL,
        department VARCHAR(100) DEFAULT NULL,
        contact VARCHAR(100) DEFAULT NULL,
        email VARCHAR(100) DEFAULT NULL,
        complaint_text TEXT NOT NULL,
        status VARCHAR(20) DEFAULT 'pending',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )"""

_ALL_TABLES = [
    ('offices', _CREATE_OFFICES_SQL),
    ('officers', _CREATE_OFFICERS_SQL),
    ('services', _CREATE_SERVICES_SQL),
    ('university_tokens', _CREATE_UNIVERSITY_TOKENS_SQL),
    ('office_messages', _CREATE_OFFICE_MESSAGES_SQL),
    ('queue_logs', _CREATE_QUEUE_LOGS_SQL),
    ('queue_counters', _CREATE_QUEUE_COUNTERS_SQL),
    ('officer_sessions', _CREATE_OFFICER_SESSIONS_SQL),
    ('officer_status_log', _CREATE_OFFICER_STATUS_LOG_SQL),
    ('general_complaints', _CREATE_GENERAL_COMPLAINTS_SQL),
]

_SEED_OFFICES_SQL = """
    INSERT IGNORE INTO offices (id, office_code, office_name, description, location, display_order)
    VALUES (1, 'AR', 'Academic Registrar Office', 'Handles registry services', 'Main Building Floor 3', 1),
           (2, 'REC', 'Records Office', 'Handles student records', 'Main Building Floor 1', 2),
           (3, 'GC', 'Guidance and Counselling', 'Student counselling services', 'COCIS Block A', 3)"""
_SEED_SERVICES_SQL = """
    INSERT IGNORE INTO services (service_code, service_name, office_id, description, estimated_time_minutes, display_order)
    VALUES ('REG', 'Registry Services', 1, 'General registry inquiries', 5, 1),
           ('TST', 'Testimonial Letters', 1, 'Request testimonials', 10, 2),
           ('GEN', 'General Inquiry', 1, 'Other academic matters', 5, 3),
           ('ADM', 'Admission Letters', 2, 'Admission support', 5, 1),
           ('TRN', 'Transcript Issuance', 2, 'Official transcripts', 20, 2),
           ('YRO', 'Year One Registration', 2, 'First year registration', 10, 3),
           ('COU', 'Counselling Session', 3, 'Student counselling', 30, 1)"""
_SEED_OFFICERS_SQL = """
    INSERT IGNORE INTO officers (officer_number, officer_name, email, phone, pin_code, office_id, is_admin, status)
    VALUES (101, 'Dr. Sarah Mukasa', 'sarah@university.ac.ug', '0700000101', '1234', 1, 0, 'available'),
           (102, 'Mr. James Okello', 'james@university.ac.ug', '0700000102', '1234', 1, 0, 'available'),
           (201, 'Ms. Grace Nambi', 'grace@university.ac.ug', '0700000201', '1234', 2, 0, 'available'),
           (202, 'Mr. Peter Ssempijja', 'peter@university.ac.ug', '0700000202', '1234', 2, 0, 'available'),
           (301, 'Ms. Alice Nakato', 'alice@university.ac.ug', '0700000301', '1234', 3, 0, 'available'),
           (999, 'System Administrator', 'admin@university.ac.ug', '0700000999', 'admin1', 1, 1, 'available')"""
_SEED_COUNTERS_SQL = """
    INSERT IGNORE INTO queue_counters (office_id, last_number)
    SELECT t.office_id, MAX(CAST(SUBSTRING(t.token_number, LENGTH(o.office_code) + 1) AS UNSIGNED))
    FROM university_tokens t JOIN offices o ON t.office_id = o.id
    GROUP BY t.office_id
    UNION ALL
    SELECT 1, 0 WHERE NOT EXISTS (SELECT 1 FROM university_tokens WHERE office_id = 1)
    UNION ALL
    SELECT 2, 0 WHERE NOT EXISTS (SELECT 1 FROM university_tokens WHERE office_id = 2)
    UNION ALL
    SELECT 3, 0 WHERE NOT EXISTS (SELECT 1 FROM university_tokens WHERE office_id = 3)"""

_ALL_INDEXES = [
    ('idx_officers_office', 'officers', 'office_id'),
    ('idx_officers_status', 'officers', 'status'),
    ('idx_officers_desk_status', 'officers', 'desk_status'),
    ('idx_services_office', 'services', 'office_id'),
    ('idx_tokens_office_status', 'university_tokens', 'office_id, status'),
    ('idx_tokens_requested', 'university_tokens', 'requested_at'),
    ('idx_tokens_service', 'university_tokens', 'service_id'),
    ('idx_tokens_student_id', 'university_tokens', 'student_id'),
    ('idx_tokens_student_unrated', 'university_tokens', 'student_id, status, feedback_submitted_at'),
    ('idx_tokens_assigned_officer', 'university_tokens', 'assigned_officer_id'),
    ('idx_tokens_feedback_submitted', 'university_tokens', 'feedback_submitted_at'),
    ('idx_tokens_called', 'university_tokens', 'called_at'),
    ('idx_tokens_serving_started', 'university_tokens', 'serving_started_at'),
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
]

# Test connection on startup
import mysql.connector as _mysql_connector
try:
    connection = mysql.connector.connect(**DB_CONFIG)
    if connection.is_connected():
        print("[OK] Successfully connected to the database")
        cursor = connection.cursor()

        # ── CREATE ALL TABLES (IF NOT EXISTS) ──
        for name, sql in _ALL_TABLES:
            cursor.execute(sql)
            connection.commit()
            print(f"[OK] Table '{name}' ready")
        
        # ── CHECK FOR MISSING COLUMNS ON EXISTING TABLES ──
        cursor.execute("SHOW COLUMNS FROM officers LIKE 'status_reason'")
        if not cursor.fetchone():
            print("[WARN] officers table missing status_reason column! Adding...")
            cursor.execute("ALTER TABLE officers ADD COLUMN status_reason TEXT DEFAULT NULL AFTER status")
            connection.commit()
            print("[OK] status_reason column added to officers")
        
        cursor.execute("SHOW COLUMNS FROM officers LIKE 'desk_status'")
        if not cursor.fetchone():
            print("[WARN] officers table missing desk_status column! Adding...")
            cursor.execute("ALTER TABLE officers ADD COLUMN desk_status ENUM('open','closed') DEFAULT 'open'")
            connection.commit()
            print("[OK] desk_status column added to officers")
        
        cursor.execute("SHOW COLUMNS FROM officers LIKE 'pin_code'")
        if not cursor.fetchone():
            print("[WARN] officers table missing pin_code column! Adding...")
            cursor.execute("ALTER TABLE officers ADD COLUMN pin_code VARCHAR(20) DEFAULT '1234'")
            connection.commit()
            print("[OK] pin_code column added to officers")

        cursor.execute("SHOW COLUMNS FROM officer_sessions LIKE 'login_location'")
        if not cursor.fetchone():
            print("[WARN] officer_sessions table missing login_location column! Adding...")
            cursor.execute("ALTER TABLE officer_sessions ADD COLUMN login_location VARCHAR(255) DEFAULT NULL AFTER login_ip")
            connection.commit()
            print("[OK] login_location column added to officer_sessions")

        cursor.execute("SHOW COLUMNS FROM officer_sessions LIKE 'logout_ip'")
        if not cursor.fetchone():
            print("[WARN] officer_sessions table missing logout_ip column! Adding...")
            cursor.execute("ALTER TABLE officer_sessions ADD COLUMN logout_ip VARCHAR(45) AFTER login_location")
            connection.commit()
            print("[OK] logout_ip column added to officer_sessions")

        cursor.execute("SHOW COLUMNS FROM general_complaints LIKE 'email'")
        if not cursor.fetchone():
            print("[WARN] general_complaints table missing email column! Adding...")
            cursor.execute("ALTER TABLE general_complaints ADD COLUMN email VARCHAR(100) DEFAULT NULL AFTER contact")
            connection.commit()
            print("[OK] email column added to general_complaints")

        # ── SEED DATA ──
        cursor.execute("SELECT COUNT(*) FROM offices")
        if cursor.fetchone()[0] == 0:
            cursor.execute(_SEED_OFFICES_SQL)
            connection.commit()
            print("[OK] Seeded offices")
        cursor.execute("SELECT COUNT(*) FROM services")
        if cursor.fetchone()[0] == 0:
            cursor.execute(_SEED_SERVICES_SQL)
            connection.commit()
            print("[OK] Seeded services")
        cursor.execute("SELECT COUNT(*) FROM officers")
        if cursor.fetchone()[0] == 0:
            cursor.execute(_SEED_OFFICERS_SQL)
            connection.commit()
            print("[OK] Seeded officers (incl. admin)")
        cursor.execute("SELECT COUNT(*) FROM queue_counters")
        if cursor.fetchone()[0] == 0:
            cursor.execute(_SEED_COUNTERS_SQL)
            connection.commit()
            print("[OK] Seeded queue counters")

        # ── INDEXES ──
        for name, table, col in _ALL_INDEXES:
            try:
                cursor.execute(f"CREATE INDEX {name} ON {table}({col})")
                connection.commit()
                print(f"[OK] Created index {name}")
            except mysql.connector.Error as e:
                if "Duplicate key name" in str(e):
                    pass
                else:
                    print(f"[WARN] Could not create index {name}: {e}")
        cursor.close()
    connection.close()
except Error as e:
    print(f"[ERROR] Error while connecting to MySQL: {e}")

# ============================================
# TTS SETUP (edge-tts)
# ============================================
_TTS_VOICE = os.environ.get('TTS_VOICE', 'en-ZA-LeahNeural')
_TTS_AVAILABLE = True
_SERVER_START = datetime.now()

try:
    import edge_tts
    print(f"[OK] Edge TTS ready (voice: {_TTS_VOICE})")
except ImportError:
    print("[WARN] edge-tts not installed. Voice announcements disabled.")
    _TTS_AVAILABLE = False


# ============================================
# SERVE HTML PAGES
# ============================================
# SERVE HTML PAGES
# ============================================
LOGIN_TOKEN = secrets.token_hex(16)
WORKFLOW_TOKEN = secrets.token_hex(16)
ADMIN_TOKEN = secrets.token_hex(16)
def _get_persistent_token(path=".officer_token"):
    try:
        with open(path) as f:
            return f.read().strip()
    except (FileNotFoundError, PermissionError):
        t = secrets.token_hex(16)
        with open(path, "w") as f:
            f.write(t)
        return t

OFFICER_TOKEN = _get_persistent_token()
FEEDBACK_TOKEN = secrets.token_hex(16)

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/index.html')
def index_html_redirect():
    return redirect('/')

@app.route('/login')
def login_decoy():
    return send_from_directory('.', '404.html'), 404

@app.route('/login/<token>')
def login_page(token):
    if token != LOGIN_TOKEN:
        return send_from_directory('.', '404.html'), 404
    return send_from_directory('.', 'login.html')

@app.route('/api/admin/login-token')
def admin_login_token():
    return jsonify({'success': True, 'token': LOGIN_TOKEN, 'url': '/login/' + LOGIN_TOKEN})

@app.route('/workflow')
def workflow_decoy():
    return send_from_directory('.', '404.html'), 404

@app.route('/workflow/<token>')
def workflow_page(token):
    if token != WORKFLOW_TOKEN:
        return send_from_directory('.', '404.html'), 404
    return send_from_directory('.', 'workflow.html')

@app.route('/api/admin/workflow-token')
def admin_workflow_token():
    return jsonify({'success': True, 'token': WORKFLOW_TOKEN, 'url': '/workflow/' + WORKFLOW_TOKEN})

@app.route('/api/admin/admin-token')
def admin_admin_token():
    return jsonify({'success': True, 'token': ADMIN_TOKEN, 'url': '/admin/' + ADMIN_TOKEN})

@app.route('/api/admin/officer-token')
def admin_officer_token():
    return jsonify({'success': True, 'token': OFFICER_TOKEN, 'url': '/officer/' + OFFICER_TOKEN})

@app.route('/api/admin/feedback-token')
def admin_feedback_token():
    return jsonify({'success': True, 'url_prefix': '/feedback.html/' + FEEDBACK_TOKEN})

@app.route('/public')
@app.route('/public-view')
def public_view_alias():
    return send_from_directory('.', 'public-display.html')

@app.route('/kiosk-setup')
def kiosk_setup():
    return send_from_directory('.', 'kiosk-setup.html')

@app.route('/download')
def download_page():
    return send_from_directory('.', 'download.html')

@app.route('/admin')
def admin_decoy():
    return send_from_directory('.', '404.html'), 404

@app.route('/admin/<token>')
def admin_dashboard(token):
    if token != ADMIN_TOKEN:
        return send_from_directory('.', '404.html'), 404
    return send_from_directory('.', 'admin-dashboard.html')

@app.route('/officer')
def officer_decoy():
    return send_from_directory('.', '404.html'), 404

@app.route('/officer/<token>')
def officer_dashboard(token):
    if token != OFFICER_TOKEN:
        return send_from_directory('.', '404.html'), 404
    return send_from_directory('.', 'officer-dashboard.html')

@app.route('/api/download/queue-kiosk-setup.exe')
def download_kiosk_installer():
    return redirect('https://github.com/amokipatr-rgb/QUeue/releases/download/v2.0.0/QueueKiosk-Setup-2.0.0.exe')

@app.route('/api/download/queue-kiosk-student-setup.exe')
def download_student_kiosk_installer():
    return redirect('https://github.com/amokipatr-rgb/QUeue/releases/download/v2.0.0/QueueKiosk-Student-Setup-2.0.0.exe')

@app.route('/api/download/queue-kiosk-index-setup.exe')
def download_index_kiosk_installer():
    return redirect('https://github.com/amokipatr-rgb/QUeue/releases/download/v2.0.0/QueueKiosk-Index-Setup-2.0.0.exe')

@app.route('/feedback.html')
def feedback_decoy():
    return send_from_directory('.', '404.html'), 404

@app.route('/feedback.html/<fb_token>')
def feedback_page_no_token(fb_token):
    if fb_token != FEEDBACK_TOKEN:
        return send_from_directory('.', '404.html'), 404
    return send_from_directory('.', 'feedback.html')

@app.route('/feedback.html/<fb_token>/<student_token>')
def feedback_page(fb_token, student_token):
    if fb_token != FEEDBACK_TOKEN:
        return send_from_directory('.', '404.html'), 404
    return send_from_directory('.', 'feedback.html')

@app.route('/student-token')
def student_token_page():
    return send_from_directory('.', 'student-token.html')

@app.route('/<path:filename>')
def serve_static(filename):
    return send_from_directory('.', filename)


# ============================================
# DATABASE HELPER
# ============================================
def get_db_connection():
    last_error = None
    for attempt in range(1, 4):
        try:
            conn = mysql.connector.connect(**DB_CONFIG)
            # test the connection is alive
            conn.ping(reconnect=True, attempts=2, delay=2)
            return conn
        except Exception as e:
            last_error = e
            logger.warning(f"[DB] Connection attempt {attempt}/3 failed: {e}")
            if attempt < 3:
                time.sleep(1)
    logger.error(f"[ERROR] Database connection error after 3 attempts: {last_error}")
    raise last_error


# ── OFFICER SESSION HELPERS ──
def auto_expire_sessions():
    """Close any active sessions that have been open for 8+ hours."""
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE officer_sessions
            SET status = 'completed',
                logout_time = DATE_ADD(login_time, INTERVAL 8 HOUR)
            WHERE status = 'active'
              AND TIMESTAMPDIFF(HOUR, login_time, NOW()) >= 8
        """)
        if cursor.rowcount:
            # Close any dangling status logs for expired sessions
            cursor.execute("""
                UPDATE officer_status_log sl
                JOIN officer_sessions s ON sl.session_id = s.id
                SET sl.ended_at = s.logout_time,
                    sl.duration_minutes = TIMESTAMPDIFF(MINUTE, sl.started_at, s.logout_time)
                WHERE sl.ended_at IS NULL AND s.status = 'completed'
            """)
            conn.commit()
    except Exception as e:
        logger.warning(f"[SESSION] Auto-expire error: {e}")
    finally:
        try: cursor.close(); conn.close()
        except: pass


def close_active_status_log(cursor, session_id, officer_id, ended_at):
    """Close the currently open status log row for a session."""
    cursor.execute("""
        UPDATE officer_status_log
        SET ended_at = %s,
            duration_minutes = TIMESTAMPDIFF(MINUTE, started_at, %s)
        WHERE session_id = %s AND officer_id = %s AND ended_at IS NULL
    """, (ended_at, ended_at, session_id, officer_id))


def open_status_log(cursor, session_id, officer_id, status, started_at):
    """Insert a new status log row."""
    cursor.execute("""
        INSERT INTO officer_status_log (session_id, officer_id, status, started_at)
        VALUES (%s, %s, %s, %s)
    """, (session_id, officer_id, status, started_at))


def get_active_session(cursor, officer_id):
    """Get the active session for an officer, or None."""
    cursor.execute("""
        SELECT id FROM officer_sessions
        WHERE officer_id = %s AND status = 'active'
        ORDER BY login_time DESC LIMIT 1
    """, (officer_id,))
    return cursor.fetchone()


# ============================================
# HEALTH CHECK
# ============================================
@app.route('/api/health', methods=['GET'])
def health_check():
    db_status = 'disconnected'
    db_error = None
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()
        cursor.close()
        conn.close()
        db_status = 'connected'
    except Exception as e:
        db_error = str(e)

    uptime = str(datetime.now() - _SERVER_START).split('.')[0]
    return jsonify({
        'status': 'ok',
        'database': db_status,
        'tts': {'available': _TTS_AVAILABLE, 'voice': _TTS_VOICE},
        'uptime': uptime,
        'started_at': _SERVER_START.isoformat(),
        'timestamp': datetime.now().isoformat(),
        'error': db_error
    })

# ============================================
# ADMIN OFFICE MANAGEMENT (CRUD)
# ============================================

@app.route('/api/admin/office', methods=['POST'])
def admin_create_office():
    """Create a new office"""
    data = request.get_json()
    
    office_code = data.get('office_code')
    office_name = data.get('office_name')
    location = data.get('location')
    description = data.get('description')
    
    if not office_code or not office_name:
        return jsonify({'success': False, 'message': 'Office code and name are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM offices WHERE office_code = %s", (office_code,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': f'Office code {office_code} already exists'}), 400
        
        cursor.execute("SELECT MAX(display_order) as max_order FROM offices")
        max_order = cursor.fetchone()
        display_order = (max_order['max_order'] or 0) + 1
        
        availability_status = (data.get('availability_status') or 'available').strip().lower()
        if availability_status not in ('available', 'unavailable'):
            availability_status = 'available'
        unavailability_notice = (data.get('unavailability_notice') or '').strip() or None
        if availability_status == 'available':
            unavailability_notice = None

        cursor.execute("""
            INSERT INTO offices (office_code, office_name, location, description, display_order,
                is_active, availability_status, unavailability_notice)
            VALUES (%s, %s, %s, %s, %s, 1, %s, %s)
        """, (office_code, office_name, location, description, display_order,
              availability_status, unavailability_notice))
        
        conn.commit()
        new_id = cursor.lastrowid
        
        return jsonify({
            'success': True, 
            'message': 'Office created successfully',
            'id': new_id
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating office: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/office/<int:office_id>', methods=['PUT'])
def admin_update_office(office_id):
    """Update an existing office"""
    data = request.get_json()
    
    office_code = data.get('office_code')
    office_name = data.get('office_name')
    location = data.get('location')
    description = data.get('description')
    is_active = data.get('is_active', 1)
    availability_status = (data.get('availability_status') or 'available').strip().lower()
    if availability_status not in ('available', 'unavailable'):
        availability_status = 'available'
    unavailability_notice_raw = data.get('unavailability_notice')
    if unavailability_notice_raw is None:
        unavailability_notice = None
    else:
        unavailability_notice = (unavailability_notice_raw or '').strip() or None
    
    if not office_code or not office_name:
        return jsonify({'success': False, 'message': 'Office code and name are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, availability_status FROM offices WHERE id = %s", (office_id,))
        office = cursor.fetchone()
        if not office:
            return jsonify({'success': False, 'message': 'Office not found'}), 404
        
        old_status = office.get('availability_status') or 'available'
        
        cursor.execute("SELECT id FROM offices WHERE office_code = %s AND id != %s", (office_code, office_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': f'Office code {office_code} already exists'}), 400
        
        if availability_status == 'available':
            unavailability_notice = None

        if availability_status == 'unavailable' and old_status != 'unavailable':
            cursor.execute("SELECT COUNT(*) AS cnt FROM university_tokens WHERE office_id = %s AND status = 'waiting'", (office_id,))
            row = cursor.fetchone()
            waiting_count = row['cnt'] if row else 0
            if waiting_count > 0:
                return jsonify({'success': False, 'message': f'Cannot close office — {waiting_count} student(s) still waiting. Serve them first.'}), 400

        cursor.execute("""
            UPDATE offices 
            SET office_code = %s, office_name = %s, location = %s, 
                description = %s, is_active = %s,
                availability_status = %s, unavailability_notice = %s
            WHERE id = %s
        """, (office_code, office_name, location, description, is_active,
              availability_status, unavailability_notice, office_id))
        
        if old_status != availability_status:
            officer_id = data.get('officer_id')
            reason = data.get('reason') or ''
            action_details = f"Availability changed from '{old_status}' to '{availability_status}'"
            if reason:
                action_details += f". Reason: {reason}"
            if officer_id:
                action_details += f" (by officer #{officer_id})"
            cursor.execute("""
                INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
                VALUES ('SYSTEM', %s, 'availability_change', %s, NOW())
            """, (officer_id, action_details))
            cursor.execute("""
                UPDATE offices SET availability_updated_at = NOW() WHERE id = %s
            """, (office_id,))

        conn.commit()
        
        return jsonify({'success': True, 'message': 'Office updated successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating office: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/office/<int:office_id>', methods=['DELETE'])
def admin_delete_office(office_id):
    """Delete an office and all associated data"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, office_code FROM offices WHERE id = %s", (office_id,))
        office = cursor.fetchone()
        if not office:
            return jsonify({'success': False, 'message': 'Office not found'}), 404
        
        cursor.execute("DELETE FROM university_tokens WHERE office_id = %s", (office_id,))
        cursor.execute("""
            DELETE FROM queue_logs 
            WHERE officer_id IN (SELECT id FROM officers WHERE office_id = %s)
        """, (office_id,))
        cursor.execute("DELETE FROM office_messages WHERE office_id = %s", (office_id,))
        cursor.execute("DELETE FROM services WHERE office_id = %s", (office_id,))
        cursor.execute("DELETE FROM officers WHERE office_id = %s", (office_id,))
        cursor.execute("DELETE FROM offices WHERE id = %s", (office_id,))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': f'Office {office["office_code"]} deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting office: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================
# ADMIN SERVICE MANAGEMENT
# ============================================

@app.route('/api/admin/service', methods=['POST'])
def admin_create_service():
    """Create a new service under an office"""
    data = request.get_json()
    
    service_code = data.get('service_code')
    service_name = data.get('service_name')
    office_id = data.get('office_id')
    description = data.get('description')
    estimated_time_minutes = data.get('estimated_time_minutes', 5)
    display_order = data.get('display_order', 0)
    
    if not service_code or not service_name:
        return jsonify({'success': False, 'message': 'Service code and service name are required'}), 400
    
    if not office_id:
        return jsonify({'success': False, 'message': 'Office ID is required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id, office_name FROM offices WHERE id = %s", (office_id,))
        office = cursor.fetchone()
        if not office:
            return jsonify({'success': False, 'message': 'Office not found'}), 404
        
        cursor.execute("""
            SELECT id FROM services 
            WHERE service_code = %s AND office_id = %s
        """, (service_code, office_id))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': f'Service code {service_code} already exists for this office'}), 400
        
        cursor.execute("""
            INSERT INTO services (service_code, service_name, office_id, description, estimated_time_minutes, display_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, (service_code, service_name, office_id, description, estimated_time_minutes, display_order))
        
        conn.commit()
        new_id = cursor.lastrowid
        
        return jsonify({
            'success': True, 
            'message': f'Service {service_name} added to {office["office_name"]} successfully',
            'id': new_id
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/service/<int:service_id>', methods=['PUT'])
def admin_update_service(service_id):
    """Update an existing service"""
    data = request.get_json()
    
    service_code = data.get('service_code')
    service_name = data.get('service_name')
    description = data.get('description')
    estimated_time_minutes = data.get('estimated_time_minutes')
    is_active = data.get('is_active', 1)
    display_order = data.get('display_order', 0)
    
    if not service_code or not service_name:
        return jsonify({'success': False, 'message': 'Service code and service name are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Service not found'}), 404
        
        cursor.execute("""
            UPDATE services 
            SET service_code = %s, service_name = %s, description = %s,
                estimated_time_minutes = %s, is_active = %s, display_order = %s
            WHERE id = %s
        """, (service_code, service_name, description, estimated_time_minutes, is_active, display_order, service_id))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Service updated successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/service/<int:service_id>', methods=['DELETE'])
def admin_delete_service(service_id):
    """Delete a service"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM services WHERE id = %s", (service_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Service not found'}), 404
        
        cursor.execute("UPDATE university_tokens SET service_id = NULL WHERE service_id = %s", (service_id,))
        cursor.execute("DELETE FROM services WHERE id = %s", (service_id,))
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Service deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting service: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/office/<int:office_id>/reset', methods=['POST'])
def admin_reset_office_queue(office_id):
    """Reset queue for a specific office (caller must match office or hold admin flag in DB)."""
    data = request.get_json() or {}
    officer_id = data.get('officer_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        if not officer_id:
            return jsonify({'success': False, 'message': 'Officer identifier required'}), 400

        cursor.execute("SELECT office_id, COALESCE(is_admin, 0) AS is_admin FROM officers WHERE id=%s", (officer_id,))
        officer = cursor.fetchone()
        if not officer:
            return jsonify({'success': False, 'message': 'Officer not found'}), 404
        if not officer.get('is_admin') and officer['office_id'] != office_id:
            return jsonify({'success': False, 'message': 'Not authorised to reset this office queue'}), 403

        cursor.execute("SELECT id, office_code, office_name FROM offices WHERE id=%s", (office_id,))
        office = cursor.fetchone()
        
        if not office:
            return jsonify({'success': False, 'message': 'Office not found'}), 404
        
        cursor.execute("""
            UPDATE university_tokens
            SET status = 'expired'
            WHERE office_id = %s AND status IN ('waiting', 'called')
        """, (office_id,))
        
        cursor.execute("""
            DELETE FROM university_tokens
            WHERE office_id = %s 
            AND requested_at >= CURDATE()
            AND status IN ('expired', 'skipped')
        """, (office_id,))
        
        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES ('SYSTEM', %s, 'queue_reset', 
                    CONCAT('Queue reset for ', %s, ' - Counter reset. Next token will be ', %s, '01'), NOW())
        """, (officer_id, office['office_name'], office['office_code']))
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'message': f'Queue reset for {office["office_name"]}. Next token will be {office["office_code"]}01',
            'next_token': f'{office["office_code"]}01'
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error resetting office queue: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================
# ADMIN OFFICER MANAGEMENT
# ============================================

@app.route('/api/admin/officer', methods=['POST'])
def admin_create_officer():
    """Create a new officer"""
    data = request.get_json()
    
    officer_number = data.get('officer_number')
    officer_name = data.get('officer_name')
    email = data.get('email')
    phone = data.get('phone')
    office_id = data.get('office_id')
    pin_code = data.get('pin_code', '1234')
    
    if not officer_number or not officer_name or not office_id:
        return jsonify({'success': False, 'message': 'Officer number, name, and office_id are required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM offices WHERE id = %s", (office_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Office not found'}), 404
        
        cursor.execute("SELECT id FROM officers WHERE officer_number = %s", (officer_number,))
        if cursor.fetchone():
            return jsonify({'success': False, 'message': f'Officer number {officer_number} already exists'}), 400
        
        cursor.execute("""
            INSERT INTO officers (officer_number, officer_name, email, phone, office_id, pin_code, status, is_admin)
            VALUES (%s, %s, %s, %s, %s, %s, 'available', 0)
        """, (officer_number, officer_name, email, phone, office_id, pin_code))
        
        conn.commit()
        new_id = cursor.lastrowid
        
        return jsonify({
            'success': True, 
            'message': 'Officer created successfully',
            'id': new_id
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error creating officer: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/officer/<int:officer_id>', methods=['PUT'])
def admin_update_officer(officer_id):
    """Update an existing officer"""
    data = request.get_json()
    
    officer_number = data.get('officer_number')
    officer_name = data.get('officer_name')
    email = data.get('email')
    phone = data.get('phone')
    office_id = data.get('office_id')
    pin_code = data.get('pin_code')
    status = data.get('status')
    
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM officers WHERE id = %s", (officer_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Officer not found'}), 404
        
        update_fields = []
        params = []
        
        if officer_number:
            update_fields.append("officer_number = %s")
            params.append(officer_number)
        if officer_name:
            update_fields.append("officer_name = %s")
            params.append(officer_name)
        if email is not None:
            update_fields.append("email = %s")
            params.append(email)
        if phone is not None:
            update_fields.append("phone = %s")
            params.append(phone)
        if office_id:
            update_fields.append("office_id = %s")
            params.append(office_id)
        if pin_code:
            update_fields.append("pin_code = %s")
            params.append(pin_code)
        if status:
            update_fields.append("status = %s")
            params.append(status)
        if data.get('status_reason') is not None:
            update_fields.append("status_reason = %s")
            params.append(data['status_reason'])
        
        if update_fields:
            params.append(officer_id)
            query = f"UPDATE officers SET {', '.join(update_fields)} WHERE id = %s"
            cursor.execute(query, params)

        # Track officer status changes in session log
        if status and status in ('available', 'offline', 'calling', 'serving'):
            try:
                cursor.execute("""
                    SELECT id FROM officer_sessions
                    WHERE officer_id = %s AND status = 'active'
                    ORDER BY login_time DESC LIMIT 1
                """, (officer_id,))
                sess = cursor.fetchone()
                if sess:
                    now = datetime.now()
                    close_active_status_log(cursor, sess['id'], officer_id, now)
                    open_status_log(cursor, sess['id'], officer_id, status, now)
                    conn.commit()
            except Exception as se:
                logger.warning(f"[SESSION] Failed to log status change: {se}")

        conn.commit()
        
        return jsonify({'success': True, 'message': 'Officer updated successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error updating officer: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/officer/<int:officer_id>', methods=['DELETE'])
def admin_delete_officer(officer_id):
    """Delete an officer"""
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    
    try:
        cursor.execute("SELECT id FROM officers WHERE id = %s", (officer_id,))
        if not cursor.fetchone():
            return jsonify({'success': False, 'message': 'Officer not found'}), 404
        
        cursor.execute("DELETE FROM queue_logs WHERE officer_id = %s", (officer_id,))
        cursor.execute("DELETE FROM office_messages WHERE officer_id = %s", (officer_id,))
        cursor.execute("UPDATE university_tokens SET assigned_officer_id = NULL WHERE assigned_officer_id = %s", (officer_id,))
        cursor.execute("DELETE FROM officers WHERE id = %s", (officer_id,))
        
        conn.commit()
        
        return jsonify({'success': True, 'message': 'Officer deleted successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error deleting officer: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/office/<int:office_id>/toggle', methods=['POST'])
def admin_toggle_office_active(office_id):
    """Toggle office active status"""
    data = request.get_json()
    is_active = data.get('is_active')
    
    if is_active is None:
        return jsonify({'success': False, 'message': 'is_active field required'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute("UPDATE offices SET is_active = %s WHERE id = %s", (is_active, office_id))
        conn.commit()
        
        status_text = "activated" if is_active else "deactivated"
        return jsonify({'success': True, 'message': f'Office {status_text} successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error toggling office: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/office/reorder', methods=['POST'])
def admin_reorder_offices():
    """Update display order of offices"""
    data = request.get_json()
    orders = data.get('orders', [])
    
    if not orders:
        return jsonify({'success': False, 'message': 'No order data provided'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        placeholders = ",".join(["%s"] * len(orders))
        case_whens = " ".join("WHEN %s THEN %s" for _ in orders)
        params = []
        for item in orders:
            params.append(item['id'])
            params.append(item['order'])
        params.extend(item['id'] for item in orders)
        cursor.execute(f"""
            UPDATE offices SET display_order = CASE id {case_whens} END
            WHERE id IN ({placeholders})
        """, params)

        conn.commit()
        return jsonify({'success': True, 'message': 'Office order updated successfully'})
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error reordering offices: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================
# PUBLIC ENDPOINTS
# ============================================

@app.route('/api/offices', methods=['GET'])
def get_offices():
    try:
        public_only = request.args.get('public_only', '').strip().lower() in ('1', 'true', 'yes')
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        where = ["COALESCE(is_active, 1) = 1"]
        params = []
        if public_only:
            where.append(
                "LOWER(COALESCE(NULLIF(TRIM(availability_status), ''), 'available')) = 'available'"
            )
        where_sql = " AND ".join(where)
        cursor.execute(f"""
            SELECT id, office_code, office_name, description, location, is_active, display_order,
                COALESCE(NULLIF(TRIM(availability_status), ''), 'available') AS availability_status,
                unavailability_notice
            FROM offices
            WHERE {where_sql}
            ORDER BY display_order
        """, tuple(params))
        offices = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'offices': offices})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/offices/all', methods=['GET'])
def get_all_offices_with_services():
    """Get all offices with their services for the kiosk"""
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        
        cursor.execute("""
            SELECT id, office_code, office_name, description, location, is_active, display_order,
                COALESCE(NULLIF(TRIM(availability_status), ''), 'available') AS availability_status,
                unavailability_notice
            FROM offices
            WHERE COALESCE(is_active, 1) = 1
              AND LOWER(COALESCE(NULLIF(TRIM(availability_status), ''), 'available')) = 'available'
            ORDER BY display_order
        """)
        offices = cursor.fetchall()
        
        for office in offices:
            cursor.execute("""
                SELECT id, service_code, service_name, description, estimated_time_minutes
                FROM services
                WHERE office_id = %s AND is_active = 1
                ORDER BY display_order
            """, (office['id'],))
            office['services'] = cursor.fetchall()
        
        cursor.close()
        conn.close()
        
        return jsonify({'success': True, 'offices': offices})
        
    except Exception as e:
        logger.error(f"Error getting offices with services: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/offices/<int:office_id>/services', methods=['GET'])
def get_office_services(office_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, service_code, service_name, description, 
                   estimated_time_minutes, is_active, display_order
            FROM services
            WHERE office_id = %s AND is_active = 1
            ORDER BY display_order
        """, (office_id,))
        services = cursor.fetchall()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'services': services})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


# ============================================
# STUDENT TOKEN GENERATION
# ============================================
@app.route('/api/student/token', methods=['POST'])
def generate_student_token():
    data = request.get_json()

    office_id = data.get('office_id')
    service_id = data.get('service_id')
    service_code = data.get('service_code')
    student_name = data.get('student_name')
    student_id = data.get('student_id')
    student_phone = data.get('student_phone')
    parent_name = data.get('parent_name')
    parent_phone = data.get('parent_phone')

    is_priority = 1 if service_code and service_code.upper() == 'PS' else 0

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, office_code, office_name, location,
                COALESCE(NULLIF(TRIM(availability_status), ''), 'available') AS availability_status,
                unavailability_notice
            FROM offices
            WHERE id = %s AND COALESCE(is_active, 1) = 1
        """, (office_id,))
        office = cursor.fetchone()

        if not office:
            return jsonify({'success': False, 'message': 'Office not available'}), 400

        if str(office.get('availability_status') or 'available').strip().lower() == 'unavailable':
            hint = office.get('unavailability_notice') or 'This office is temporarily unavailable for new tickets.'
            return jsonify({'success': False, 'message': hint}), 400

        cursor.execute("""
            SELECT id, service_name, estimated_time_minutes 
            FROM services 
            WHERE id = %s AND is_active = 1
        """, (service_id,))
        service = cursor.fetchone()

        if not service:
            return jsonify({'success': False, 'message': 'Service not available'}), 400

        cursor.execute("""
            SELECT COUNT(*) as cnt 
            FROM officers
            WHERE office_id = %s AND status != 'offline'
        """, (office_id,))
        officer_check = cursor.fetchone()

        if not officer_check or officer_check['cnt'] == 0:
            return jsonify({
                'success': False,
                'message': 'No officers available for this office right now'
            }), 400

        # Block if student has an unrated completed token
        if student_id and student_id.strip():
            cursor.execute("""
                SELECT token_number
                FROM university_tokens
                WHERE student_id = %s
                  AND status IN ('completed', 'waiting')
                  AND feedback_submitted_at IS NULL
                ORDER BY requested_at DESC
                LIMIT 1
            """, (student_id.strip(),))
            unrated = cursor.fetchone()
            if unrated:
                return jsonify({
                    'success': False,
                    'blocked': True,
                    'unrated_token': unrated['token_number'],
                    'message': f"Please rate your previous service (Token: {unrated['token_number']}) before getting a new token."
                }), 400

        cursor.execute("INSERT IGNORE INTO queue_counters (office_id, last_number) VALUES (%s, 0)", (office_id,))
        cursor.execute("""
            UPDATE queue_counters
            SET last_number = LAST_INSERT_ID(last_number + 1)
            WHERE office_id = %s
        """, (office_id,))
        cursor.execute("SELECT LAST_INSERT_ID() AS next_num")
        result = cursor.fetchone()
        next_num = result['next_num']
        token_number = f"{office['office_code']}{str(next_num).zfill(2)}"

        print(f"Token generated: {token_number} (counter={next_num})")

        cursor.execute("""
            SELECT COUNT(*) as ahead_count
            FROM university_tokens
            WHERE office_id = %s AND status = 'waiting'
        """, (office_id,))

        ahead = cursor.fetchone()
        ahead_count = ahead['ahead_count'] if ahead else 0

        queue_position = ahead_count + 1
        estimated_wait = ahead_count * service['estimated_time_minutes']

        cursor.execute("""
            INSERT INTO university_tokens
                (token_number, office_id, service_id, service_code,
                 student_name, student_id, student_phone,
                 parent_name, parent_phone, is_priority,
                 status, queue_position, estimated_wait_minutes, source, requested_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s,
                    %s, %s, %s,
                    'waiting', %s, %s, 'kiosk', NOW())
        """, (
            token_number,
            office_id,
            service_id,
            service_code,
            student_name,
            student_id,
            student_phone,
            parent_name,
            parent_phone,
            is_priority,
            queue_position,
            estimated_wait
        ))

        conn.commit()

        return jsonify({
            'success': True,
            'token_number': token_number,
            'office_name': office['office_name'],
            'service_name': service['service_name'],
            'location': office.get('location', 'Main Campus'),
            'queue_position': queue_position,
            'ahead_count': ahead_count,
            'estimated_wait': estimated_wait
        })

    except Exception as e:
        conn.rollback()
        logger.error(f"Token generation error: {e}")
        logger.error(traceback.format_exc())

        return jsonify({
            'success': False,
            'message': 'Internal server error'
        }), 500

    finally:
        cursor.close()
        conn.close()


# ============================================
# STUDENT TOKEN LOOKUP (for feedback)
# ============================================
@app.route('/api/student/token-info', methods=['GET'])
def get_token_info():
    token_number = request.args.get('token_number')

    if not token_number:
        return jsonify({'success': False, 'message': 'Token number required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT t.token_number, t.student_name, t.status, t.rating,
                   t.feedback_submitted_at, t.completed_at,
                   off.office_name, off.office_code,
                   s.service_name
            FROM university_tokens t
            JOIN offices off ON t.office_id = off.id
            LEFT JOIN services s ON t.service_id = s.id
            WHERE t.token_number = %s
        """, (token_number,))
        token = cursor.fetchone()

        if not token:
            return jsonify({'success': False, 'message': 'Token not found'}), 404

        return jsonify({
            'success': True,
            'token': {
                'token_number': token['token_number'],
                'student_name': token['student_name'],
                'status': token['status'],
                'office_name': token['office_name'],
                'office_code': token['office_code'],
                'service_name': token['service_name'],
                'completed_at': token['completed_at'].isoformat() if isinstance(token.get('completed_at'), datetime) else token.get('completed_at'),
                'rating': token.get('rating'),
                'feedback_submitted': token.get('feedback_submitted_at') is not None
            }
        })

    except Exception as e:
        logger.error(f"Token info error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================
# QR REDIRECT (opaque URL for receipts)
# ============================================
@app.route('/r/<token>')
def rate_redirect(token):
    return redirect('/feedback.html/' + FEEDBACK_TOKEN + '/' + token)


# ============================================
# STUDENT FEEDBACK / RATING
# ============================================
@app.route('/api/student/feedback', methods=['POST'])
def submit_feedback():
    data = request.get_json()

    token_number = data.get('token_number')
    rating = data.get('rating')
    feedback_text = data.get('feedback_text', '').strip()

    if not token_number:
        return jsonify({'success': False, 'message': 'Token number is required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)

    try:
        cursor.execute("""
            SELECT id, office_id, status, rating, feedback_submitted_at
            FROM university_tokens
            WHERE token_number = %s
        """, (token_number,))
        token = cursor.fetchone()

        if not token:
            return jsonify({'success': False, 'message': 'Token not found'}), 404

        if token.get('feedback_submitted_at') is not None:
            return jsonify({'success': False, 'message': 'Feedback already submitted for this token'}), 400

        is_completed = token['status'] == 'completed'

        if is_completed:
            if rating is None or not isinstance(rating, int) or rating < 1 or rating > 5:
                return jsonify({'success': False, 'message': 'Rating must be 1-5'}), 400
        else:
            if not feedback_text:
                return jsonify({'success': False, 'message': 'Please describe your issue or complaint'}), 400
            if rating is None or not isinstance(rating, int) or rating < 1 or rating > 5:
                rating = 0

        cursor.execute("""
            UPDATE university_tokens
            SET rating = %s, feedback_text = %s, feedback_submitted_at = NOW()
            WHERE id = %s
        """, (rating, feedback_text or None, token['id']))

        conn.commit()

        msg = 'Thank you for your feedback!' if is_completed else 'We have received your complaint and will look into it.'
        return jsonify({'success': True, 'message': msg})

    except Exception as e:
        conn.rollback()
        logger.error(f"Feedback submission error: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': 'Internal server error'}), 500

    finally:
        cursor.close()
        conn.close()


# ============================================
# GENERAL COMPLAINT (non-token)
# ============================================
@app.route('/api/student/general-complaint', methods=['POST'])
def submit_general_complaint():
    data = request.get_json()
    category = data.get('category')
    complaint_text = data.get('complaint_text', '').strip()
    email = (data.get('email') or '').strip()

    if not category or category not in ('Student', 'Staff', 'Other'):
        return jsonify({'success': False, 'message': 'Valid category is required'}), 400
    if not complaint_text:
        return jsonify({'success': False, 'message': 'Please describe your complaint'}), 400
    if not email:
        return jsonify({'success': False, 'message': 'Email address is required for follow-up'}), 400

    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO general_complaints
                (category, full_name, student_number, employee_id, department, contact, email, complaint_text)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            category,
            data.get('full_name'),
            data.get('student_number') if category == 'Student' else None,
            data.get('employee_id') if category == 'Staff' else None,
            data.get('department'),
            data.get('contact') if category == 'Other' else None,
            email,
            complaint_text
        ))
        conn.commit()
        return jsonify({'success': True, 'message': 'Your complaint has been received. We will look into it.'})
    except Exception as e:
        conn.rollback()
        logger.error(f"General complaint error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/general-complaints')
def admin_get_general_complaints():
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, category, full_name, student_number, employee_id,
                   department, contact, email, complaint_text, status, created_at
            FROM general_complaints
            ORDER BY created_at DESC
        """)
        complaints = cursor.fetchall()
        for c in complaints:
            c['created_at'] = c['created_at'].isoformat() if c['created_at'] else None
        return jsonify({'success': True, 'data': complaints})
    except Exception as e:
        logger.error(f"Fetch general complaints error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/general-complaints/<int:complaint_id>/resolve', methods=['POST'])
def resolve_general_complaint(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("UPDATE general_complaints SET status = 'resolved' WHERE id = %s", (complaint_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Complaint marked as resolved'})
    except Exception as e:
        conn.rollback()
        logger.error(f"Resolve complaint error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/admin/general-complaints/<int:complaint_id>', methods=['DELETE'])
def delete_general_complaint(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("DELETE FROM general_complaints WHERE id = %s", (complaint_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Complaint deleted'})
    except Exception as e:
        conn.rollback()
        logger.error(f"Delete complaint error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()


def send_resolved_email(complaint):
    email_to = complaint.get('email')
    if not email_to or not SMTP_USER or not SMTP_PASS:
        return False
    try:
        msg = EmailMessage()
        msg['Subject'] = f"Your Complaint #{complaint['id']} has been Resolved — SMQSS"
        msg['From'] = SMTP_FROM
        msg['To'] = email_to
        msg.set_content(f"""Dear {complaint.get('full_name') or 'Valued Customer'},

Thank you for reaching out to us regarding your concern at Makerere University.

We are pleased to inform you that your complaint (ID: #{complaint['id']}) has been reviewed and resolved.

Complaint Summary:
{complaint.get('complaint_text', '')}

If you have any further concerns, please don't hesitate to reach out. We appreciate your patience and understanding.

Best regards,
Makerere University Queue Management System (SMQSS)
""")
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as s:
            s.starttls()
            s.login(SMTP_USER, SMTP_PASS)
            s.send_message(msg)
        logger.info(f"Resolved email sent to {email_to} for complaint #{complaint['id']}")
        return True
    except Exception as e:
        logger.error(f"Failed to send resolved email for complaint #{complaint['id']}: {e}")
        return False


@app.route('/api/admin/general-complaints/<int:complaint_id>/notify', methods=['POST'])
def notify_general_complaint(complaint_id):
    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT id, category, full_name, email, complaint_text, status
            FROM general_complaints WHERE id = %s
        """, (complaint_id,))
        complaint = cursor.fetchone()
        if not complaint:
            return jsonify({'success': False, 'message': 'Complaint not found'}), 404

        sent = send_resolved_email(complaint)
        if sent:
            return jsonify({'success': True, 'message': f'Notification email sent to {complaint["email"]}'})
        else:
            return jsonify({'success': False, 'message': 'Failed to send email. Check SMTP config or recipient address.'}), 500
    except Exception as e:
        logger.error(f"Notify complaint error: {e}")
        return jsonify({'success': False, 'message': 'Internal server error'}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================
# OFFICER LOGIN
# ============================================
@app.route('/api/officer/login', methods=['POST'])
def officer_login():
    data = request.get_json()
    officer_number = data.get('officer_number')
    pin_code = data.get('pin_code')

    if not officer_number or not pin_code:
        return jsonify({'success': False, 'message': 'Officer number and PIN required'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT o.id, o.officer_number, o.officer_name, o.office_id,
                   o.status, o.status_reason, o.is_admin,
                   off.office_code, off.office_name, off.location
            FROM officers o
            JOIN offices off ON o.office_id = off.id
            WHERE o.officer_number = %s AND o.pin_code = %s
        """, (officer_number, pin_code))
        officer = cursor.fetchone()

        if not officer:
            return jsonify({'success': False, 'message': 'Invalid number or PIN'}), 401

        role = 'admin' if officer.get('is_admin') else 'officer'

        # auto-expire stale sessions first
        auto_expire_sessions()

        # create a new session
        try:
            now = datetime.now()
            device = request.headers.get('User-Agent', '')[:255]
            location = geoip(request.remote_addr)
            cursor.execute("""
                INSERT INTO officer_sessions (officer_id, office_id, session_date, login_time, login_ip, login_location, device_info, status)
                VALUES (%s, %s, CURDATE(), %s, %s, %s, %s, %s)
            """, (officer['id'], officer['office_id'], now, request.remote_addr, location, device, 'active'))
            conn.commit()
        except Exception as se:
            logger.warning(f"[SESSION] Failed to create login session: {se}")

        return jsonify({
            'success': True,
            'user': {
                'id': officer['id'],
                'officer_number': officer['officer_number'],
                'officer_name': officer['officer_name'],
                'office_id': officer['office_id'],
                'office_code': officer['office_code'],
                'office_name': officer['office_name'],
                'location': officer.get('location', ''),
                'status': officer['status'],
                'status_reason': officer.get('status_reason') or '',
                'role': role,
                'user_type': role
            }
        })

    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()




# ============================================
# OFFICER QUEUE
# ============================================
@app.route('/api/officer/queue/<int:officer_id>', methods=['GET'])
def get_officer_queue(officer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT o.id, o.officer_name, o.office_id, o.status, o.current_token,
                   off.office_code, off.office_name, off.location
            FROM officers o
            JOIN offices off ON o.office_id = off.id
            WHERE o.id = %s
        """, (officer_id,))
        officer = cursor.fetchone()
        if not officer:
            return jsonify({'success': False, 'message': 'Officer not found'})

        cursor.execute("""
            SELECT t.id, t.token_number, t.student_name, t.student_id, t.student_phone,
                   t.service_code, t.parent_phone, t.requested_at,
                   s.service_name,
                   TIMESTAMPDIFF(MINUTE, t.requested_at, NOW()) as waiting_minutes
            FROM university_tokens t
            LEFT JOIN services s ON t.service_id = s.id
            WHERE t.office_id = %s AND t.status = 'waiting'
            ORDER BY t.is_priority DESC, t.requested_at ASC
        """, (officer['office_id'],))
        waiting = cursor.fetchall()

        cursor.execute("""
            SELECT t.token_number, t.status, t.called_at, t.serving_started_at,
                   t.service_code, s.service_name, t.student_name
            FROM university_tokens t
            LEFT JOIN services s ON t.service_id = s.id
            WHERE t.office_id = %s AND t.status IN ('called','serving')
            ORDER BY t.called_at DESC LIMIT 1
        """, (officer['office_id'],))
        current = cursor.fetchone()

        cursor.execute("""
            SELECT COUNT(*) as cnt FROM university_tokens
            WHERE office_id = %s
              AND status = 'completed'
              AND DATE(completed_at) = CURDATE()
        """, (officer['office_id'],))
        completed_row = cursor.fetchone()
        completed_today = completed_row['cnt'] if completed_row else 0

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'waiting': waiting,
            'current': current,
            'office_code': officer['office_code'],
            'office_name': officer['office_name'],
            'location': officer.get('location', ''),
            'completed_today': completed_today
        })

    except Exception as e:
        logger.error(f"Error in get_officer_queue: {e}")
        return jsonify({'success': False, 'message': str(e)})


# ============================================
# PUBLIC QUEUES
# ============================================
@app.route('/api/public/queues', methods=['GET'])
def get_public_queues():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, office_code, office_name, location,
                COALESCE(NULLIF(TRIM(availability_status), ''), 'available') AS availability_status,
                unavailability_notice
            FROM offices
            WHERE COALESCE(is_active, 1) = 1
            ORDER BY display_order
        """)
        offices = cursor.fetchall()

        result = []
        for office in offices:
            cursor.execute("""
                SELECT t.token_number, t.student_name
                FROM university_tokens t
                WHERE t.office_id = %s AND t.status = 'called'
                ORDER BY t.called_at DESC LIMIT 1
            """, (office['id'],))
            called = cursor.fetchone()

            cursor.execute("""
                SELECT t.token_number, t.student_name
                FROM university_tokens t
                WHERE t.office_id = %s AND t.status = 'serving'
                ORDER BY t.serving_started_at DESC LIMIT 1
            """, (office['id'],))
            serving = cursor.fetchone()

            cursor.execute("""
                SELECT COUNT(*) as waiting_count FROM university_tokens
                WHERE office_id = %s AND status = 'waiting'
            """, (office['id'],))
            waiting_count = cursor.fetchone()

            result.append({
                'office_id': office['id'],
                'office_code': office['office_code'],
                'office_name': office['office_name'],
                'location': office.get('location', ''),
                'availability_status': office.get('availability_status') or 'available',
                'unavailability_notice': office.get('unavailability_notice'),
                'current_called': called['token_number'] if called else None,
                'called_student': called['student_name'] if called else None,
                'current_serving': serving['token_number'] if serving else None,
                'serving_student': serving['student_name'] if serving else None,
                'waiting_count': waiting_count['waiting_count'] if waiting_count else 0
            })

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'queues': result})

    except Exception as e:
        logger.error(f"Error in get_public_queues: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/public/queues/next', methods=['GET'])
def get_public_queues_next():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT id, office_code, office_name,
                   COALESCE(NULLIF(TRIM(availability_status), ''), 'available') AS availability_status
            FROM offices
            WHERE COALESCE(is_active, 1) = 1
            ORDER BY display_order
        """)
        offices = cursor.fetchall()

        # Count how many available offices have waiting tokens
        cursor.execute("""
            SELECT COUNT(DISTINCT t.office_id) as cnt
            FROM university_tokens t
            JOIN offices o ON t.office_id = o.id
            WHERE COALESCE(o.is_active, 1) = 1
            AND COALESCE(NULLIF(TRIM(o.availability_status), ''), 'available') = 'available'
            AND t.status = 'waiting'
        """)
        active_office_count = cursor.fetchone()['cnt']

        if active_office_count >= 3:
            per_office_limit = 1
        elif active_office_count == 2:
            per_office_limit = 2
        elif active_office_count == 1:
            per_office_limit = 3
        else:
            per_office_limit = 0

        result = []
        for office in offices:
            if office.get('availability_status', 'available').strip().lower() != 'available':
                continue
            if per_office_limit > 0:
                cursor.execute("""
                    SELECT t.token_number, t.student_name, t.service_code,
                           t.requested_at, t.is_priority,
                           TIMESTAMPDIFF(MINUTE, t.requested_at, NOW()) as waiting_minutes,
                           s.service_name
                    FROM university_tokens t
                    LEFT JOIN services s ON t.service_id = s.id
                    WHERE t.office_id = %s AND t.status = 'waiting'
                    ORDER BY t.is_priority DESC, t.requested_at ASC
                    LIMIT %s
                """, (office['id'], per_office_limit))
                next_tokens = cursor.fetchall()
            else:
                next_tokens = []

            result.append({
                'office_id': office['id'],
                'office_code': office['office_code'],
                'office_name': office['office_name'],
                'next_up': next_tokens
            })

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'queues': result})

    except Exception as e:
        logger.error(f"Error in get_public_queues_next: {e}")
        return jsonify({'success': False, 'message': str(e)})


# ============================================
# OFFICER ACTIONS
# ============================================

@app.route('/api/officer/call-next', methods=['POST'])
def officer_call_next():
    data = request.get_json()
    officer_id = data.get('officer_id')
    officer_number = data.get('officer_number')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT office_id FROM officers WHERE id=%s", (officer_id,))
        officer = cursor.fetchone()
        if not officer:
            return jsonify({'success': False, 'message': 'Officer not found'})

        cursor.execute("""
            SELECT token_number FROM university_tokens
            WHERE office_id = %s AND status = 'serving'
        """, (officer['office_id'],))
        current_serving = cursor.fetchone()
        
        if current_serving:
            cursor.execute("""
                UPDATE university_tokens t
                INNER JOIN officers o ON o.id = %s
                SET t.status = 'completed', t.completed_at = NOW(),
                    t.assigned_officer_id = IFNULL(t.assigned_officer_id, o.id),
                    t.assigned_officer_number = COALESCE(t.assigned_officer_number, o.officer_number)
                WHERE t.token_number = %s
            """, (officer_id, current_serving['token_number']))

        cursor.execute("""
            SELECT id, token_number, student_name, service_code 
            FROM university_tokens
            WHERE office_id=%s AND status='waiting'
            ORDER BY is_priority DESC, requested_at ASC LIMIT 1
        """, (officer['office_id'],))
        
        token = cursor.fetchone()
        if not token:
            return jsonify({'success': False, 'message': 'No students waiting'})

        cursor.execute("""
            UPDATE university_tokens
            SET status='called', called_at=NOW(),
                assigned_officer_id=%s, assigned_officer_number=%s
            WHERE id=%s
        """, (officer_id, officer_number, token['id']))

        cursor.execute("""
            UPDATE officers SET status='calling', current_token=%s, last_activity=NOW()
            WHERE id=%s
        """, (token['token_number'], officer_id))

        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES (%s, %s, 'called', CONCAT('Called from officer dashboard - Student: ', IFNULL(%s, '')), NOW())
        """, (token['token_number'], officer_id, token['student_name']))

        conn.commit()

        return jsonify({
            'success': True, 
            'token_number': token['token_number'], 
            'student_name': token['student_name'] or '', 
            'service_code': token['service_code']
        })

    except Exception as e:
        conn.rollback()
        logger.error(f"Error in call-next: {e}")
        logger.error(traceback.format_exc())
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/officer/call-specific', methods=['POST'])
def officer_call_specific():
    data = request.get_json()
    officer_id = data.get('officer_id')
    officer_number = data.get('officer_number')
    token_number = data.get('token_number')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT student_name FROM university_tokens
            WHERE token_number=%s
        """, (token_number,))
        token = cursor.fetchone()

        cursor.execute("""
            UPDATE university_tokens
            SET status='called', called_at=NOW(),
                assigned_officer_id=%s, assigned_officer_number=%s
            WHERE token_number=%s AND status='waiting'
        """, (officer_id, officer_number, token_number))

        cursor.execute("""
            UPDATE officers SET status='calling', current_token=%s, last_activity=NOW()
            WHERE id=%s
        """, (token_number, officer_id))

        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES (%s, %s, 'called', CONCAT('Called from officer dashboard - Student: ', IFNULL(%s, '')), NOW())
        """, (token_number, officer_id, token['student_name'] if token else ''))

        conn.commit()

        return jsonify({
            'success': True, 
            'token_number': token_number,
            'student_name': token['student_name'] if token else ''
        })
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in call-specific: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/officer/serve', methods=['POST'])
def officer_serve():
    data = request.get_json()
    officer_id = data.get('officer_id')
    token_number = data.get('token_number')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT t.student_name, t.office_id, off.office_name 
            FROM university_tokens t
            JOIN offices off ON t.office_id = off.id
            WHERE t.token_number = %s
        """, (token_number,))
        token_info = cursor.fetchone()
        
        if not token_info:
            return jsonify({'success': False, 'message': 'Token not found'}), 404
        
        cursor.execute("""
            UPDATE university_tokens 
            SET status='serving', serving_started_at=NOW() 
            WHERE token_number=%s
        """, (token_number,))
        
        cursor.execute("""
            UPDATE officers SET status='serving', last_activity=NOW() 
            WHERE id=%s
        """, (officer_id,))
        
        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES (%s, %s, 'serving', 
                    CONCAT('Started serving - Student: ', IFNULL(%s, '')),
                    NOW())
        """, (token_number, officer_id, token_info.get('student_name', '')))
        
        conn.commit()
        
        return jsonify({
            'success': True, 
            'student_name': token_info.get('student_name') or '',
            'office_name': token_info.get('office_name') or '',
            'token_number': token_number
        })
        
    except Exception as e:
        conn.rollback()
        logger.error(f"Error in serve: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/officer/complete', methods=['POST'])
def officer_complete():
    data = request.get_json()
    officer_id = data.get('officer_id')
    token_number = data.get('token_number')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE university_tokens t
            INNER JOIN officers o ON o.id = %s
            SET t.status = 'completed', t.completed_at = NOW(),
                t.assigned_officer_id = IFNULL(t.assigned_officer_id, o.id),
                t.assigned_officer_number = COALESCE(t.assigned_officer_number, o.officer_number)
            WHERE t.token_number = %s
        """, (officer_id, token_number))
        cursor.execute("""
            UPDATE officers SET status='available', current_token=NULL, last_activity=NOW()
            WHERE id=%s
        """, (officer_id,))

        # Increment session tokens_served
        try:
            cursor.execute("""
                UPDATE officer_sessions
                SET tokens_served = tokens_served + 1
                WHERE officer_id = %s AND status = 'active'
            """, (officer_id,))
        except Exception as se:
            logger.warning(f"[SESSION] Failed to increment tokens_served: {se}")

        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/officer/skip', methods=['POST'])
def officer_skip():
    data = request.get_json()
    officer_id = data.get('officer_id')
    token_number = data.get('token_number')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            UPDATE university_tokens 
            SET status='skipped', skipped_at=NOW() 
            WHERE token_number=%s
        """, (token_number,))
        cursor.execute("""
            UPDATE officers SET status='available', current_token=NULL, last_activity=NOW() 
            WHERE id=%s
        """, (officer_id,))
        conn.commit()
        return jsonify({'success': True})
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/officer/recall', methods=['POST'])
def officer_recall():
    data = request.get_json()
    officer_id = data.get('officer_id')
    token_number = data.get('token_number')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT student_name FROM university_tokens WHERE token_number=%s
        """, (token_number,))
        token = cursor.fetchone()
        
        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES (%s, %s, 'recall', CONCAT('Manual recall announcement - Student: ', IFNULL(%s, '')), NOW())
        """, (token_number, officer_id, token['student_name'] if token else ''))
        conn.commit()
        
        return jsonify({
            'success': True,
            'student_name': token['student_name'] if token else ''
        })
    except Exception as e:
        conn.rollback()
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/queue/recent-recalls', methods=['GET'])
def get_recent_recalls():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT l.id, l.token_number, l.officer_id, l.created_at, l.action_details,
                   off.office_code, off.office_name, t.student_name
            FROM queue_logs l
            JOIN officers o ON l.officer_id = o.id
            JOIN offices off ON o.office_id = off.id
            LEFT JOIN university_tokens t ON l.token_number = t.token_number
            WHERE l.action = 'recall' AND l.created_at >= NOW() - INTERVAL 2 MINUTE
            ORDER BY l.created_at DESC
            LIMIT 50
        """)
        recalls = cursor.fetchall()

        for r in recalls:
            if isinstance(r.get('created_at'), datetime):
                r['created_at'] = r['created_at'].isoformat()

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'recalls': recalls})

    except Exception as e:
        logger.error(f"Error in get_recent_recalls: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# OFFICE MESSAGES
# ============================================
@app.route('/api/office/message', methods=['POST'])
def post_office_message():
    data = request.get_json()
    office_id = data.get('office_id')
    message = data.get('message')
    message_type = data.get('message_type', 'info')
    officer_id = data.get('officer_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("UPDATE office_messages SET is_active=0 WHERE office_id=%s", (office_id,))
        cursor.execute("""
            INSERT INTO office_messages (office_id, message, message_type, officer_id, is_active, created_at)
            VALUES (%s, %s, %s, %s, 1, NOW())
        """, (office_id, message, message_type, officer_id))
        conn.commit()
        return jsonify({'success': True, 'message': 'Message posted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


@app.route('/api/office/messages', methods=['GET'])
def get_office_messages():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        office_id = request.args.get('office_id', type=int)
        office_code = request.args.get('office_code', type=str)
        include_inactive = request.args.get('include_inactive', default='0')
        limit = request.args.get('limit', default=50, type=int)

        if limit is None:
            limit = 50
        limit = max(1, min(limit, 200))

        where_clauses = []
        params = []

        if include_inactive != '1':
            where_clauses.append("om.is_active = 1")

        if office_id:
            where_clauses.append("om.office_id = %s")
            params.append(office_id)
        elif office_code:
            where_clauses.append("off.office_code = %s")
            params.append(office_code)

        where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""
        query = f"""
            SELECT om.id, om.office_id, om.message, om.message_type, om.created_at, 
                   off.office_name, off.office_code
            FROM office_messages om
            JOIN offices off ON om.office_id = off.id
            {where_sql}
            ORDER BY om.created_at DESC
            LIMIT %s
        """
        params.append(limit)
        cursor.execute(query, tuple(params))
        messages = cursor.fetchall()
        for m in messages:
            if isinstance(m.get('created_at'), datetime):
                m['created_at'] = m['created_at'].isoformat()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/officer/messages/<int:officer_id>', methods=['GET'])
def get_officer_messages(officer_id):
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, office_id, message, message_type, created_at, is_active
            FROM office_messages
            WHERE officer_id = %s
            ORDER BY created_at DESC
        """, (officer_id,))
        messages = cursor.fetchall()
        for m in messages:
            if isinstance(m.get('created_at'), datetime):
                m['created_at'] = m['created_at'].isoformat()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'messages': messages})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/office/message/<int:message_id>', methods=['DELETE'])
def delete_office_message(message_id):
    data = request.get_json()
    officer_id = data.get('officer_id')

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("SELECT officer_id FROM office_messages WHERE id=%s", (message_id,))
        msg = cursor.fetchone()
        if not msg:
            return jsonify({'success': False, 'message': 'Message not found'}), 404
        if msg['officer_id'] != officer_id:
            return jsonify({'success': False, 'message': 'You can only delete your own messages'}), 403
        cursor.execute("DELETE FROM office_messages WHERE id=%s", (message_id,))
        conn.commit()
        return jsonify({'success': True, 'message': 'Message deleted'})
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)}), 500
    finally:
        cursor.close()
        conn.close()


# ============================================
# OFFICER: SEARCH TOKENS
# ============================================
@app.route('/api/officer/search-tokens', methods=['GET'])
def officer_search_tokens():
    officer_id = request.args.get('officer_id', type=int)
    q = request.args.get('q', '').strip()

    if not officer_id:
        return jsonify({'success': False, 'message': 'officer_id required'}), 400
    if not q:
        return jsonify({'success': False, 'message': 'Search term required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT office_id FROM officers WHERE id = %s", (officer_id,))
        off = cursor.fetchone()
        if not off:
            return jsonify({'success': False, 'message': 'Officer not found'}), 404

        pattern = f'%{q}%'
        cursor.execute("""
            SELECT t.token_number, t.student_name, t.student_id, t.student_phone,
                   t.parent_name, t.parent_phone, t.service_code, t.is_priority,
                   t.status, t.requested_at, t.called_at, t.serving_started_at,
                   t.completed_at, t.skipped_at, t.assigned_officer_number,
                   o2.officer_name AS assigned_officer_name,
                   s.service_name,
                   off.office_name
            FROM university_tokens t
            JOIN services s ON t.service_id = s.id
            JOIN offices off ON t.office_id = off.id
            LEFT JOIN officers o2 ON t.assigned_officer_id = o2.id
            WHERE t.office_id = %s
              AND (t.token_number LIKE %s OR t.student_name LIKE %s)
            ORDER BY t.requested_at DESC
            LIMIT 50
        """, (off['office_id'], pattern, pattern))
        results = cursor.fetchall()

        for r in results:
            for col in ('requested_at', 'called_at', 'serving_started_at', 'completed_at', 'skipped_at'):
                if isinstance(r.get(col), datetime):
                    r[col] = r[col].isoformat()

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'results': results})

    except Exception as e:
        logger.error(f"Search error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# OFFICER: CHANGE PASSWORD
# ============================================
@app.route('/api/officer/change-password', methods=['POST'])
def officer_change_password():
    data = request.get_json()
    officer_id = data.get('officer_id')
    current_pin = data.get('current_pin')
    new_pin = data.get('new_pin')

    if not officer_id or not current_pin or not new_pin:
        return jsonify({'success': False, 'message': 'officer_id, current_pin, new_pin required'}), 400

    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("SELECT id, pin_code FROM officers WHERE id = %s", (officer_id,))
        officer = cursor.fetchone()
        if not officer:
            return jsonify({'success': False, 'message': 'Officer not found'}), 404
        if officer['pin_code'] != current_pin:
            return jsonify({'success': False, 'message': 'Current PIN is incorrect'}), 403

        cursor.execute("UPDATE officers SET pin_code = %s WHERE id = %s", (new_pin, officer_id))
        conn.commit()
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'message': 'PIN changed successfully'})

    except Exception as e:
        logger.error(f"Change password error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# ADMIN STATS
# ============================================
@app.route('/api/admin/stats', methods=['GET'])
def admin_get_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT 
                off.id, off.office_code, off.office_name, off.location, off.is_active,
                COALESCE(NULLIF(TRIM(off.availability_status), ''), 'available') AS availability_status,
                off.unavailability_notice,
                COUNT(CASE WHEN t.status = 'waiting' THEN 1 END) as waiting,
                COUNT(CASE WHEN t.status = 'called' THEN 1 END) as called,
                COUNT(CASE WHEN t.status = 'serving' THEN 1 END) as serving,
                COUNT(CASE WHEN t.status = 'completed' AND t.requested_at >= CURDATE() THEN 1 END) as completed,
                COUNT(CASE WHEN t.status = 'skipped' AND t.requested_at >= CURDATE() THEN 1 END) as skipped
            FROM offices off
            LEFT JOIN university_tokens t ON off.id = t.office_id
                AND (t.requested_at >= CURDATE() OR t.status IN ('waiting','called','serving'))
            GROUP BY off.id
            ORDER BY off.display_order
        """)
        stats = cursor.fetchall()

        cursor.execute("""
            SELECT o.id, o.officer_number, o.officer_name, o.status, o.current_token,
                   o.status_reason, o.email, o.phone, o.office_id,
                   off.office_name, off.office_code
            FROM officers o
            JOIN offices off ON o.office_id = off.id
            WHERE o.is_admin = 0 OR o.is_admin IS NULL
            ORDER BY off.display_order, o.officer_number
        """)
        officers = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'stats': stats, 'officers': officers})
    except Exception as e:
        logger.error(f"Error in admin_get_stats: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/admin/daily-stats', methods=['GET'])
def admin_daily_stats():
    try:
        target_date = request.args.get('date')

        if not target_date:
            target_date = datetime.now().strftime('%Y-%m-%d')

        start = f"{target_date} 00:00:00"
        end = f"{target_date} 23:59:59"

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                off.id,
                off.office_code,
                off.office_name,
                off.location,
                COUNT(CASE WHEN t.requested_at BETWEEN %s AND %s THEN 1 END) AS total_tokens,
                COUNT(CASE WHEN t.called_at BETWEEN %s AND %s THEN 1 END) AS tokens_called,
                COUNT(CASE WHEN t.serving_started_at BETWEEN %s AND %s THEN 1 END) AS service_started_count,
                COUNT(CASE WHEN t.completed_at BETWEEN %s AND %s THEN 1 END) AS completed,
                COUNT(CASE WHEN t.skipped_at BETWEEN %s AND %s THEN 1 END) AS skipped,
                COUNT(CASE WHEN t.status = 'waiting' THEN 1 END) AS current_waiting,
                COUNT(CASE WHEN t.status = 'serving' THEN 1 END) AS currently_serving,
                ROUND(AVG(CASE WHEN t.completed_at BETWEEN %s AND %s THEN TIMESTAMPDIFF(MINUTE, t.requested_at, t.completed_at) END), 1) AS avg_turnaround_minutes,
                ROUND(AVG(CASE WHEN t.completed_at BETWEEN %s AND %s THEN TIMESTAMPDIFF(MINUTE, t.serving_started_at, t.completed_at) END), 1) AS avg_service_minutes,
                ROUND(AVG(CASE WHEN t.serving_started_at BETWEEN %s AND %s THEN TIMESTAMPDIFF(MINUTE, t.requested_at, t.serving_started_at) END), 1) AS avg_queue_wait_before_service_minutes,
                ROUND(AVG(CASE WHEN t.called_at BETWEEN %s AND %s THEN TIMESTAMPDIFF(MINUTE, t.called_at, t.serving_started_at) END), 1) AS avg_response_after_call_minutes
            FROM offices off
            LEFT JOIN university_tokens t ON off.id = t.office_id
            WHERE off.is_active = 1
            GROUP BY off.id
            ORDER BY off.display_order
        """, (
            start, end, start, end, start, end, start, end, start, end,
            start, end, start, end, start, end, start, end
        ))

        offices = cursor.fetchall()

        for row in offices:
            completed = row.get('completed') or 0
            skipped = row.get('skipped') or 0
            closed = completed + skipped
            row['completion_rate'] = round((completed / closed) * 100, 1) if closed > 0 else 0

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'date': target_date,
            'offices': offices
        })

    except Exception as e:
        logger.error(f"Error in admin_daily_stats: {e}")
        return jsonify({'success': False, 'message': str(e)})


@app.route('/api/admin/officer-service-stats', methods=['GET'])
def admin_officer_service_stats():
    """Per officer: users (tokens) completed on a given day, grouped by active office."""
    target_date = request.args.get('date')
    if not target_date:
        target_date = datetime.now().strftime('%Y-%m-%d')
    try:
        datetime.strptime(target_date, '%Y-%m-%d')
    except ValueError:
        return jsonify({'success': False, 'message': 'Invalid date; use YYYY-MM-DD'}), 400

    conn = get_db_connection()
    cursor = conn.cursor(dictionary=True)
    try:
        cursor.execute("""
            SELECT
                off.id AS office_id,
                off.office_code,
                off.office_name,
                COALESCE(NULLIF(TRIM(off.availability_status), ''), 'available') AS office_availability_status,
                off.unavailability_notice AS office_unavailability_notice,
                off.availability_updated_at AS office_availability_updated_at,
                o.id AS officer_id,
                o.officer_number,
                o.officer_name,
                o.status AS active_status,
                o.status_reason,
                COALESCE(cnt.served_count, 0) AS served_count
            FROM officers o
            INNER JOIN offices off ON o.office_id = off.id AND COALESCE(off.is_active, 1) = 1
            LEFT JOIN (
                SELECT assigned_officer_id, COUNT(*) AS served_count
                FROM university_tokens
                WHERE status = 'completed'
                  AND completed_at >= %s
                  AND completed_at < %s + INTERVAL 1 DAY
                  AND assigned_officer_id IS NOT NULL
                GROUP BY assigned_officer_id
            ) cnt ON cnt.assigned_officer_id = o.id
            WHERE COALESCE(o.is_admin, 0) = 0
            ORDER BY off.display_order, off.office_name, o.officer_number
        """, (target_date, target_date))
        rows = cursor.fetchall()
        for row in rows:
            sc = row.get('served_count')
            row['served_count'] = int(sc) if sc is not None else 0
            on = row.get('officer_number')
            row['officer_number'] = int(on) if on is not None else None
            if row.get('active_status'):
                row['active_status'] = str(row['active_status'])
            ast = row.get('office_availability_status')
            row['office_availability_status'] = str(ast or 'available').strip().lower()
            onc = row.get('office_unavailability_notice')
            row['office_unavailability_notice'] = str(onc) if onc not in (None, '') else ''
        cursor.close()
        conn.close()
        return jsonify({'success': True, 'date': target_date, 'officers': rows})
    except Exception as e:
        logger.error(f"Error in admin_officer_service_stats: {e}")
        try:
            cursor.close()
            conn.close()
        except Exception:
            pass
        return jsonify({'success': False, 'message': str(e)})


# ============================================
# ADMIN: FEEDBACK / RATINGS
# ============================================
@app.route('/api/admin/feedback', methods=['GET'])
def admin_get_feedback():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                t.token_number, t.student_name, t.student_id,
                t.status, t.rating, t.feedback_text, t.feedback_submitted_at,
                off.office_name, off.office_code,
                o.officer_name AS officer_name,
                o.officer_number AS officer_number
            FROM university_tokens t
            JOIN offices off ON t.office_id = off.id
            LEFT JOIN officers o ON t.assigned_officer_id = o.id
            WHERE t.feedback_submitted_at IS NOT NULL
            ORDER BY t.feedback_submitted_at DESC
        """)
        feedback = cursor.fetchall()

        for f in feedback:
            f['rating'] = int(f['rating']) if f['rating'] is not None else None
            f['officer_number'] = int(f['officer_number']) if f['officer_number'] is not None else None
            if isinstance(f.get('feedback_submitted_at'), datetime):
                f['feedback_submitted_at'] = f['feedback_submitted_at'].isoformat()

        cursor.close()
        conn.close()

        return jsonify({'success': True, 'feedback': feedback})

    except Exception as e:
        logger.error(f"Error fetching feedback: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/feedback/stats', methods=['GET'])
def admin_feedback_stats():
    try:
        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Overall aggregates
        cursor.execute("""
            SELECT
                COUNT(*) AS total_submissions,
                SUM(CASE WHEN rating > 0 THEN 1 ELSE 0 END) AS total_ratings,
                SUM(CASE WHEN rating = 0 THEN 1 ELSE 0 END) AS total_complaints,
                ROUND(AVG(CASE WHEN rating > 0 THEN rating END), 2) AS avg_rating
            FROM university_tokens
            WHERE feedback_submitted_at IS NOT NULL
        """)
        overall = cursor.fetchone()
        overall['total_submissions'] = int(overall['total_submissions'])
        overall['total_ratings'] = int(overall['total_ratings'])
        overall['total_complaints'] = int(overall['total_complaints'])
        overall['avg_rating'] = float(overall['avg_rating']) if overall['avg_rating'] is not None else 0
        overall['complaint_ratio'] = round(
            overall['total_complaints'] / overall['total_submissions'] * 100, 1
        ) if overall['total_submissions'] else 0

        # Rating distribution (1-5 stars)
        cursor.execute("""
            SELECT rating, COUNT(*) AS count
            FROM university_tokens
            WHERE feedback_submitted_at IS NOT NULL AND rating > 0
            GROUP BY rating
            ORDER BY rating
        """)
        dist_rows = cursor.fetchall()
        distribution = {str(r): 0 for r in range(1, 6)}
        for row in dist_rows:
            distribution[str(int(row['rating']))] = int(row['count'])

        # Per-office stats
        cursor.execute("""
            SELECT
                off.id, off.office_name, off.office_code,
                COUNT(*) AS submission_count,
                ROUND(AVG(CASE WHEN t.rating > 0 THEN t.rating END), 2) AS avg_rating,
                SUM(CASE WHEN t.rating > 0 THEN 1 ELSE 0 END) AS rating_count,
                SUM(CASE WHEN t.rating = 0 THEN 1 ELSE 0 END) AS complaint_count
            FROM university_tokens t
            JOIN offices off ON t.office_id = off.id
            WHERE t.feedback_submitted_at IS NOT NULL
            GROUP BY off.id, off.office_name, off.office_code
            ORDER BY submission_count DESC
        """)
        by_office = []
        for row in cursor.fetchall():
            by_office.append({
                'id': row['id'],
                'office_name': row['office_name'],
                'office_code': row['office_code'],
                'submission_count': int(row['submission_count']),
                'avg_rating': float(row['avg_rating']) if row['avg_rating'] is not None else 0,
                'rating_count': int(row['rating_count']),
                'complaint_count': int(row['complaint_count']),
            })

        # Per-officer stats
        cursor.execute("""
            SELECT
                o.id, o.officer_name, o.officer_number,
                off.office_name, off.office_code,
                COUNT(*) AS submission_count,
                ROUND(AVG(CASE WHEN t.rating > 0 THEN t.rating END), 2) AS avg_rating,
                SUM(CASE WHEN t.rating > 0 THEN 1 ELSE 0 END) AS rating_count,
                SUM(CASE WHEN t.rating = 0 THEN 1 ELSE 0 END) AS complaint_count
            FROM university_tokens t
            JOIN offices off ON t.office_id = off.id
            JOIN officers o ON t.assigned_officer_id = o.id
            WHERE t.feedback_submitted_at IS NOT NULL
            GROUP BY o.id, o.officer_name, o.officer_number, off.office_name, off.office_code
            ORDER BY submission_count DESC
        """)
        by_officer = []
        for row in cursor.fetchall():
            by_officer.append({
                'id': row['id'],
                'officer_name': row['officer_name'],
                'officer_number': int(row['officer_number']),
                'office_name': row['office_name'],
                'office_code': row['office_code'],
                'submission_count': int(row['submission_count']),
                'avg_rating': float(row['avg_rating']) if row['avg_rating'] is not None else 0,
                'rating_count': int(row['rating_count']),
                'complaint_count': int(row['complaint_count']),
            })

        # Daily trend (last 30 days)
        cursor.execute("""
            SELECT
                DATE(feedback_submitted_at) AS day,
                COUNT(*) AS submissions,
                ROUND(AVG(CASE WHEN rating > 0 THEN rating END), 2) AS avg_rating
            FROM university_tokens
            WHERE feedback_submitted_at IS NOT NULL
                AND feedback_submitted_at >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
            GROUP BY DATE(feedback_submitted_at)
            ORDER BY day
        """)
        trend = []
        for row in cursor.fetchall():
            trend.append({
                'day': row['day'].isoformat() if isinstance(row.get('day'), datetime) else str(row['day']),
                'submissions': int(row['submissions']),
                'avg_rating': float(row['avg_rating']) if row['avg_rating'] is not None else 0,
            })

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'overall': overall,
            'distribution': distribution,
            'by_office': by_office,
            'by_officer': by_officer,
            'trend': trend,
        })

    except Exception as e:
        logger.error(f"Error fetching feedback stats: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# OFFICER ATTENDANCE
# ============================================
@app.route('/api/admin/officer-attendance', methods=['GET'])
def admin_officer_attendance():
    """Weekly attendance for all officers. Accepts ?week=YYYY-MM-DD (Monday of that week)."""
    try:
        week_start = request.args.get('week', '')
        if not week_start:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        week_end_dt = datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=4)
        week_end = week_end_dt.strftime('%Y-%m-%d')
        fmt_dt = '%Y-%m-%d %H:%i:%s'

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                o.id AS officer_id,
                o.officer_number,
                o.officer_name,
                off.id AS office_id,
                off.office_code,
                off.office_name,
                off.location,
                s.id AS session_id,
                s.session_date,
                DATE_FORMAT(s.login_time, %s) AS login_time,
                DATE_FORMAT(s.logout_time, %s) AS logout_time,
                s.login_ip,
                s.logout_ip,
                s.login_location,
                s.device_info,
                s.tokens_served,
                TIMESTAMPDIFF(MINUTE, s.login_time, COALESCE(s.logout_time, NOW())) AS duration_minutes
            FROM officers o
            JOIN offices off ON o.office_id = off.id
            LEFT JOIN officer_sessions s ON o.id = s.officer_id
                AND s.session_date BETWEEN %s AND %s
            ORDER BY o.officer_name, s.session_date
        """, (fmt_dt, fmt_dt, week_start, week_end))

        rows = cursor.fetchall()
        # Group by officer
        officers_map = {}
        for row in rows:
            oid = row['officer_id']
            if oid not in officers_map:
                officers_map[oid] = {
                    'officer_id': oid,
                    'officer_number': row['officer_number'],
                    'officer_name': row['officer_name'],
                    'office_id': row['office_id'],
                    'office_code': row['office_code'],
                    'office_name': row['office_name'],
                    'location': row['location'],
                    'days': {}
                }
            sd = str(row['session_date']) if row['session_date'] else None
            if sd:
                if sd not in officers_map[oid]['days']:
                    officers_map[oid]['days'][sd] = []
                officers_map[oid]['days'][sd].append({
                    'session_id': row['session_id'],
                    'login_time': row['login_time'],
                    'logout_time': row['logout_time'],
                    'login_ip': row['login_ip'],
                    'logout_ip': row['logout_ip'],
                    'login_location': row['login_location'],
                    'device_info': row['device_info'],
                    'tokens_served': row['tokens_served'] or 0,
                    'duration_minutes': row['duration_minutes'] or 0,
                })

        # Compute weekly totals
        result = []
        for oid, odata in officers_map.items():
            total_minutes = 0
            total_served = 0
            days_present = 0
            day_details = []
            for d in range(5):
                date_key = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=d)).strftime('%Y-%m-%d')
                sessions = odata['days'].get(date_key, [])
                day_minutes = sum(s['duration_minutes'] for s in sessions)
                day_served = sum(s['tokens_served'] for s in sessions)
                if sessions:
                    days_present += 1
                    total_minutes += day_minutes
                    total_served += day_served
                    last = sessions[-1]
                    day_details.append({
                        'date': date_key,
                        'present': True,
                        'sessions': sessions,
                        'total_minutes': day_minutes,
                        'tokens_served': day_served,
                        'device_info': last.get('device_info') or '',
                        'login_ip': last.get('login_ip') or '',
                        'login_location': last.get('login_location') or '',
                    })
                else:
                    day_details.append({
                        'date': date_key,
                        'present': False,
                        'sessions': [],
                        'total_minutes': 0,
                        'tokens_served': 0,
                        'device_info': '',
                        'login_ip': '',
                        'login_location': '',
                    })
            DAILY_TARGET = 540  # 9 hours (8 AM – 5 PM)
            WEEKLY_TARGET = DAILY_TARGET * 5
            avail_pct = min(round(total_minutes / WEEKLY_TARGET * 100, 1), 100)

            if days_present == 0:
                continue

            result.append({
                'officer_id': oid,
                'officer_number': odata['officer_number'],
                'officer_name': odata['officer_name'],
                'office_code': odata['office_code'],
                'office_name': odata['office_name'],
                'location': odata['location'],
                'days': day_details,
                'total_minutes': total_minutes,
                'total_hours': round(total_minutes / 60, 1),
                'tokens_served': total_served,
                'days_present': days_present,
                'availability_pct': avail_pct,
            })

        # Monthly attendance grade for the current month
        today = datetime.now()
        month_start = today.replace(day=1).strftime('%Y-%m-%d')
        next_month = today.replace(day=1) + timedelta(days=32)
        month_end = next_month.replace(day=1) - timedelta(days=1)
        month_end_str = month_end.strftime('%Y-%m-%d')

        _, days_in_month = monthrange(today.year, today.month)
        working_days = sum(1 for d in range(1, days_in_month + 1) if datetime(today.year, today.month, d).weekday() < 5)
        MONTHLY_TARGET = 540 * working_days

        cursor.execute("""
            SELECT officer_id,
                   SUM(TIMESTAMPDIFF(MINUTE, login_time, COALESCE(logout_time, NOW()))) AS month_minutes
            FROM officer_sessions
            WHERE session_date BETWEEN %s AND %s
            GROUP BY officer_id
        """, (month_start, month_end_str))
        monthly_rows = cursor.fetchall()
        monthly_map = {r['officer_id']: (r['month_minutes'] or 0) for r in monthly_rows}

        for entry in result:
            month_minutes = monthly_map.get(entry['officer_id'], 0)
            entry['monthly_grade_pct'] = min(round(month_minutes / MONTHLY_TARGET * 100, 1), 100)

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'attendance': result, 'week_start': week_start, 'week_end': week_end})

    except Exception as e:
        logger.error(f"Error fetching attendance: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/officer-attendance/<int:officer_id>', methods=['GET'])
def admin_officer_attendance_detail(officer_id):
    """Detailed session history for one officer. Accepts ?from=YYYY-MM-DD&to=YYYY-MM-DD"""
    try:
        from_date = request.args.get('from', (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d'))
        to_date = request.args.get('to', datetime.now().strftime('%Y-%m-%d'))
        fmt_dt = '%Y-%m-%d %H:%i:%s'

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                s.id AS session_id,
                s.session_date,
                DATE_FORMAT(s.login_time, %s) AS login_time,
                DATE_FORMAT(s.logout_time, %s) AS logout_time,
                s.login_ip, s.logout_ip, s.login_location, s.device_info,
                s.tokens_served,
                TIMESTAMPDIFF(MINUTE, s.login_time, COALESCE(s.logout_time, NOW())) AS duration_minutes,
                off.office_name, off.office_code, off.location
            FROM officer_sessions s
            JOIN offices off ON s.office_id = off.id
            WHERE s.officer_id = %s AND s.session_date BETWEEN %s AND %s
            ORDER BY s.login_time DESC
        """, (fmt_dt, fmt_dt, officer_id, from_date, to_date))

        sessions = cursor.fetchall()

        # Get status breakdown for each session
        for sess in sessions:
            cursor.execute("""
                SELECT status,
                       DATE_FORMAT(started_at, %s) AS started_at,
                       DATE_FORMAT(ended_at, %s) AS ended_at,
                       duration_minutes
                FROM officer_status_log
                WHERE session_id = %s
                ORDER BY started_at
            """, (fmt_dt, fmt_dt, sess['session_id']))
            sess['status_log'] = cursor.fetchall()

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'officer_id': officer_id, 'sessions': sessions})

    except Exception as e:
        logger.error(f"Error fetching officer attendance detail: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/attendance-summary', methods=['GET'])
def admin_attendance_summary():
    """Weekly aggregated attendance summary. Accepts ?week=YYYY-MM-DD"""
    try:
        week_start = request.args.get('week', '')
        if not week_start:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        week_end = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=4)).strftime('%Y-%m-%d')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                o.id AS officer_id,
                o.officer_number,
                o.officer_name,
                off.office_code,
                off.office_name,
                off.location,
                COUNT(DISTINCT s.session_date) AS days_attended,
                COALESCE(SUM(TIMESTAMPDIFF(MINUTE, s.login_time, COALESCE(s.logout_time, NOW()))), 0) AS total_minutes,
                COALESCE(SUM(s.tokens_served), 0) AS total_tokens,
                ROUND(COUNT(DISTINCT s.session_date) / 5 * 100, 1) AS attendance_pct,
                ROUND(COALESCE(SUM(TIMESTAMPDIFF(MINUTE, s.login_time, COALESCE(s.logout_time, NOW()))), 0) / 60, 1) AS total_hours,
                CASE WHEN COUNT(DISTINCT s.session_date) > 0
                     THEN ROUND(COALESCE(SUM(s.tokens_served), 0) * 60.0 / NULLIF(SUM(TIMESTAMPDIFF(MINUTE, s.login_time, COALESCE(s.logout_time, NOW()))), 0), 1)
                     ELSE 0 END AS tokens_per_hour
            FROM officers o
            JOIN offices off ON o.office_id = off.id
            LEFT JOIN officer_sessions s ON o.id = s.officer_id
                AND s.session_date BETWEEN %s AND %s
            GROUP BY o.id, o.officer_number, o.officer_name, off.office_code, off.office_name, off.location
            ORDER BY attendance_pct DESC, total_tokens DESC
        """, (week_start, week_end))

        summary = cursor.fetchall()
        for row in summary:
            row['total_minutes'] = int(row['total_minutes'])
            row['total_tokens'] = int(row['total_tokens'])
            row['days_attended'] = int(row['days_attended'])
            row['attendance_pct'] = float(row['attendance_pct'])
            row['total_hours'] = float(row['total_hours'])
            row['tokens_per_hour'] = float(row['tokens_per_hour'])

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'summary': summary, 'week_start': week_start, 'week_end': week_end})

    except Exception as e:
        logger.error(f"Error fetching attendance summary: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# HEAT MAP
# ============================================
@app.route('/api/admin/heatmap', methods=['GET'])
def admin_heatmap():
    """Hourly demand/officer/wait heat map. ?week=YYYY-MM-DD&office_id=INT&metric=tokens|wait|officers"""
    try:
        week_start = request.args.get('week', '')
        office_id = request.args.get('office_id', type=int)
        metric = request.args.get('metric', 'tokens')

        if not week_start:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        # Get offices
        if office_id:
            cursor.execute("SELECT id, office_code, office_name FROM offices WHERE id = %s", (office_id,))
        else:
            cursor.execute("SELECT id, office_code, office_name FROM offices WHERE is_active = 1")
        offices = cursor.fetchall()

        days_of_week = []
        for d in range(5):
            day = (datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=d)).strftime('%Y-%m-%d')
            days_of_week.append(day)

        hours = list(range(8, 17))  # 8am to 5pm (hour 8-16)

        result = []
        for off in offices:
            days_data = []
            for day_str in days_of_week:
                hour_data = []
                for hr in hours:
                    if metric == 'tokens':
                        cursor.execute("""
                            SELECT COUNT(*) AS val FROM university_tokens
                            WHERE office_id = %s AND DATE(requested_at) = %s AND HOUR(requested_at) = %s
                        """, (off['id'], day_str, hr))
                        row = cursor.fetchone()
                        val = int(row['val']) if row else 0
                    elif metric == 'wait':
                        cursor.execute("""
                            SELECT COALESCE(AVG(wait_duration_minutes), 0) AS val FROM university_tokens
                            WHERE office_id = %s AND DATE(requested_at) = %s AND HOUR(requested_at) = %s
                              AND wait_duration_minutes IS NOT NULL
                        """, (off['id'], day_str, hr))
                        row = cursor.fetchone()
                        val = round(float(row['val']), 1) if row else 0
                    elif metric == 'officers':
                        hr_start = f"{day_str} {hr:02d}:00:00"
                        hr_end = f"{day_str} {hr:02d}:59:59"
                        cursor.execute("""
                            SELECT COUNT(DISTINCT officer_id) AS val FROM officer_sessions
                            WHERE office_id = %s AND status = 'active'
                              AND login_time <= %s AND (logout_time IS NULL OR logout_time >= %s)
                        """, (off['id'], hr_end, hr_start))
                        row = cursor.fetchone()
                        val = int(row['val']) if row else 0
                    else:
                        val = 0

                    hour_data.append({
                        'hour': hr,
                        'value': val,
                        'label': f"{hr:02d}:00"
                    })
                days_data.append({
                    'date': day_str,
                    'day': ['Mon','Tue','Wed','Thu','Fri'][days_of_week.index(day_str)],
                    'hours': hour_data
                })
            result.append({
                'office_id': off['id'],
                'office_code': off['office_code'],
                'office_name': off['office_name'],
                'days': days_data
            })

        # Compute summary
        all_vals = []
        for off_data in result:
            for dd in off_data['days']:
                for hh in dd['hours']:
                    all_vals.append(hh['value'])
        max_val = max(all_vals) if all_vals else 1

        peak_hour = None
        peak_total = 0
        for hr in hours:
            total = 0
            for off_data in result:
                for dd in off_data['days']:
                    for hh in dd['hours']:
                        if hh['hour'] == hr:
                            total += hh['value']
            if total > peak_total:
                peak_total = total
                peak_hour = f"{hr:02d}:00"

        busiest_office = max(result, key=lambda o: sum(hh['value'] for dd in o['days'] for hh in dd['hours'])) if result else None

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'week_start': week_start,
            'metric': metric,
            'max_value': max_val,
            'offices': result,
            'summary': {
                'peak_hour': peak_hour,
                'busiest_office': busiest_office['office_name'] if busiest_office else None,
                'hours': hours,
                'days': ['Mon','Tue','Wed','Thu','Fri']
            }
        })

    except Exception as e:
        logger.error(f"Error fetching heatmap: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# ATTENDANCE TRENDS
# ============================================
@app.route('/api/admin/attendance-trends', methods=['GET'])
def admin_attendance_trends():
    """Weekly trend data. ?weeks=8"""
    try:
        num_weeks = request.args.get('weeks', 8, type=int)
        today = datetime.now()
        end_date = today.strftime('%Y-%m-%d')

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        weeks_data = []
        for w in range(num_weeks):
            week_end = (today - timedelta(weeks=w)).strftime('%Y-%m-%d')
            week_start_dt = datetime.strptime(week_end, '%Y-%m-%d') - timedelta(days=4)
            week_start = week_start_dt.strftime('%Y-%m-%d')

            # Tokens created in this week
            cursor.execute("""
                SELECT COUNT(*) AS total FROM university_tokens
                WHERE requested_at BETWEEN %s AND %s
            """, (week_start + ' 00:00:00', week_end + ' 23:59:59'))
            tokens_created = int(cursor.fetchone()['total'])

            # Total officer hours logged
            cursor.execute("""
                SELECT COALESCE(SUM(TIMESTAMPDIFF(MINUTE, login_time, COALESCE(logout_time, NOW()))), 0) AS total_minutes
                FROM officer_sessions
                WHERE session_date BETWEEN %s AND %s
            """, (week_start, week_end))
            total_minutes = int(cursor.fetchone()['total_minutes'])

            # Unique officers who logged in
            cursor.execute("""
                SELECT COUNT(DISTINCT officer_id) AS cnt FROM officer_sessions
                WHERE session_date BETWEEN %s AND %s
            """, (week_start, week_end))
            active_officers = int(cursor.fetchone()['cnt'])

            # Avg wait time
            cursor.execute("""
                SELECT COALESCE(AVG(wait_duration_minutes), 0) AS avg_wait FROM university_tokens
                WHERE requested_at BETWEEN %s AND %s AND wait_duration_minutes IS NOT NULL
            """, (week_start + ' 00:00:00', week_end + ' 23:59:59'))
            avg_wait = round(float(cursor.fetchone()['avg_wait']), 1)

            # Avg service time
            cursor.execute("""
                SELECT COALESCE(AVG(service_duration_minutes), 0) AS avg_service FROM university_tokens
                WHERE completed_at BETWEEN %s AND %s AND service_duration_minutes IS NOT NULL
            """, (week_start + ' 00:00:00', week_end + ' 23:59:59'))
            avg_service = round(float(cursor.fetchone()['avg_service']), 1)

            weeks_data.append({
                'week_start': week_start,
                'week_end': week_end,
                'label': f"W{datetime.strptime(week_start, '%Y-%m-%d').isocalendar()[1]}",
                'tokens_created': tokens_created,
                'total_hours': round(total_minutes / 60, 1),
                'active_officers': active_officers,
                'avg_wait_minutes': avg_wait,
                'avg_service_minutes': avg_service,
            })

        weeks_data.reverse()

        # Per-office demand over weeks
        cursor.execute("""
            SELECT off.id, off.office_code, off.office_name
            FROM offices off WHERE off.is_active = 1
        """)
        all_offices = cursor.fetchall()

        office_trends = []
        for off in all_offices:
            weekly = []
            for w in range(num_weeks):
                week_end = (today - timedelta(weeks=w)).strftime('%Y-%m-%d')
                week_start = (datetime.strptime(week_end, '%Y-%m-%d') - timedelta(days=4)).strftime('%Y-%m-%d')
                cursor.execute("""
                    SELECT COUNT(*) AS cnt FROM university_tokens
                    WHERE office_id = %s AND requested_at BETWEEN %s AND %s
                """, (off['id'], week_start + ' 00:00:00', week_end + ' 23:59:59'))
                weekly.append(int(cursor.fetchone()['cnt']))
            weekly.reverse()
            office_trends.append({
                'office_id': off['id'],
                'office_code': off['office_code'],
                'office_name': off['office_name'],
                'weekly_tokens': weekly
            })

        # Top officers by attendance
        cursor.execute("""
            SELECT o.id, o.officer_name, o.officer_number,
                   COUNT(DISTINCT s.session_date) AS days_attended,
                   COALESCE(SUM(TIMESTAMPDIFF(MINUTE, s.login_time, COALESCE(s.logout_time, NOW()))), 0) AS total_minutes,
                   COALESCE(SUM(s.tokens_served), 0) AS total_served
            FROM officer_sessions s
            JOIN officers o ON s.officer_id = o.id
            WHERE s.session_date >= %s
            GROUP BY o.id, o.officer_name, o.officer_number
            ORDER BY days_attended DESC, total_minutes DESC
            LIMIT 10
        """, ((today - timedelta(days=num_weeks * 7)).strftime('%Y-%m-%d'),))
        top_officers = cursor.fetchall()
        for row in top_officers:
            row['total_minutes'] = int(row['total_minutes'])
            row['total_served'] = int(row['total_served'])
            row['days_attended'] = int(row['days_attended'])

        cursor.close()
        conn.close()

        return jsonify({
            'success': True,
            'weeks': weeks_data,
            'office_trends': office_trends,
            'top_officers': top_officers,
        })

    except Exception as e:
        logger.error(f"Error fetching attendance trends: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


@app.route('/api/admin/attendance-log', methods=['GET'])
def admin_attendance_log():
    """Flat event log of all In/Out clock events for a given week."""
    try:
        week_start = request.args.get('week', '')
        if not week_start:
            today = datetime.now()
            week_start = (today - timedelta(days=today.weekday())).strftime('%Y-%m-%d')

        week_end_dt = datetime.strptime(week_start, '%Y-%m-%d') + timedelta(days=4)
        week_end = week_end_dt.strftime('%Y-%m-%d')
        fmt_dt = '%Y-%m-%d %H:%i:%s'

        conn = get_db_connection()
        cursor = conn.cursor(dictionary=True)

        cursor.execute("""
            SELECT
                s.id AS session_id,
                DATE_FORMAT(s.login_time, %s) AS login_time,
                DATE_FORMAT(s.logout_time, %s) AS logout_time,
                s.login_location,
                s.device_info,
                o.id AS officer_id,
                o.officer_name,
                o.officer_number,
                off.office_name,
                off.location AS office_location
            FROM officer_sessions s
            JOIN officers o ON s.officer_id = o.id
            JOIN offices off ON s.office_id = off.id
            WHERE s.session_date BETWEEN %s AND %s
            ORDER BY s.login_time, s.id
        """, (fmt_dt, fmt_dt, week_start, week_end))

        rows = cursor.fetchall()
        log = []
        for row in rows:
            device = 'Desktop'
            ua = (row['device_info'] or '')
            s = ua.lower()
            if re.search(r'(iphone|ipod|opera mini|blackberry|android.*mobile)', s):
                device = 'Mobile'
            elif re.search(r'(ipad|tablet|playbook|silk|android(?!.*mobile))', s):
                device = 'Tablet'

            log.append({
                'datetime': row['login_time'],
                'type': 'In',
                'location': row['login_location'] or 'N/A',
                'office_name': row['office_name'],
                'office_location': row['office_location'] or '',
                'device': device,
                'officer_name': row['officer_name'],
                'officer_number': row['officer_number'],
            })
            if row['logout_time']:
                log.append({
                    'datetime': row['logout_time'],
                    'type': 'Out',
                    'location': row['login_location'] or 'N/A',
                    'office_name': row['office_name'],
                    'office_location': row['office_location'] or '',
                    'device': device,
                    'officer_name': row['officer_name'],
                    'officer_number': row['officer_number'],
                })

        cursor.close()
        conn.close()
        return jsonify({'success': True, 'log': log, 'week_start': week_start, 'week_end': week_end})

    except Exception as e:
        logger.error(f"Error fetching attendance log: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# TEXT-TO-SPEECH (edge-tts)
# ============================================
@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    if not _TTS_AVAILABLE:
        return jsonify({'success': False, 'message': 'TTS engine not available'}), 503

    data = request.get_json()
    text = data.get('text', '').strip()

    if not text:
        return jsonify({'success': False, 'message': 'Text is required'}), 400

    try:
        async def _synthesize():
            tts = edge_tts.Communicate(text, _TTS_VOICE)
            audio = b""
            async for chunk in tts.stream():
                if chunk["type"] == "audio":
                    audio += chunk["data"]
            return audio

        audio_data = asyncio.run(_synthesize())

        if not audio_data:
            return jsonify({'success': False, 'message': 'No audio generated'}), 500

        return audio_data, 200, {'Content-Type': 'audio/mpeg'}

    except Exception as e:
        logger.error(f"TTS error: {e}")
        return jsonify({'success': False, 'message': str(e)}), 500


# ============================================
# WSGI ENTRY POINT (for Gunicorn / Railway)
# ============================================
application = app

# ============================================
# RUN APPLICATION
# ============================================
if __name__ == '__main__':
    PORT = int(os.environ.get('PORT', 5000))

    # Run session expiry on startup + schedule every 5 minutes
    import threading
    def session_cleanup_loop():
        while True:
            try:
                auto_expire_sessions()
            except Exception:
                pass
            time.sleep(300)

    t = threading.Thread(target=session_cleanup_loop, daemon=True)
    t.start()

    print("=" * 55)
    print("SMQSS — Smart Queue Management System API (Piloted at Makerere University)")
    print("=" * 55)
    print(f"Server starting on port {PORT}")
    print()
    print("Office Hierarchy Enabled:")
    print("  - Academic Registrar Office (AR) -> Registry, Testimonials, General")
    print("  - Records Office (REC) -> Admission Letters, Year One Registration, Transcripts")
    print()
    print("Features:")
    print("  - Student token generation with office + service selection")
    print("  - Officer dashboard with service-aware queue")
    print("  - Public display with real-time called tokens")
    print("  - Voice announcements for called/serving tokens")
    print("  - Recall logging for public display synchronization")
    print()
    print(f"  >>> Login URL: http://127.0.0.1:{PORT}/login/{LOGIN_TOKEN}")
    print(f"  >>> Workflow URL: http://127.0.0.1:{PORT}/workflow/{WORKFLOW_TOKEN}")
    print(f"  >>> Admin URL: http://127.0.0.1:{PORT}/admin/{ADMIN_TOKEN}")
    print(f"  >>> Officer URL: http://127.0.0.1:{PORT}/officer/{OFFICER_TOKEN}")
    print(f"  >>> Feedback URL: http://127.0.0.1:{PORT}/feedback.html/{FEEDBACK_TOKEN}/TOKEN")
    print("=" * 55)
    app.run(host='0.0.0.0', port=PORT, debug=os.environ.get('FLASK_ENV') == 'development')