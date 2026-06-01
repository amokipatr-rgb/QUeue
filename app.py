from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import mysql.connector
from mysql.connector import Error
from datetime import datetime, timedelta
import logging
import os
import traceback
import asyncio
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# ============================================
# DATABASE CONFIGURATION
# ============================================
DB_CONFIG = {
    'host': os.environ.get('MYSQL_HOST', 'localhost'),
    'port': int(os.environ.get('MYSQL_PORT', 3306)),
    'user': os.environ.get('MYSQL_USER', 'root'),
    'password': os.environ.get('MYSQL_PASSWORD', ''),
    'database': os.environ.get('MYSQL_DATABASE', 'db')
}

# Test connection on startup
try:
    connection = mysql.connector.connect(**DB_CONFIG)
    if connection.is_connected():
        print("[OK] Successfully connected to the database")
        
        # Check if queue_logs table exists
        cursor = connection.cursor()
        cursor.execute("SHOW TABLES LIKE 'queue_logs'")
        if not cursor.fetchone():
            print("[WARN] queue_logs table missing! Creating...")
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS queue_logs (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    token_number VARCHAR(20),
                    officer_id INT,
                    action VARCHAR(50),
                    action_details TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    INDEX idx_action_created (action, created_at)
                )
            """)
            connection.commit()
            print("[OK] queue_logs table created")
        # Check if officers table has status_reason column
        cursor.execute("SHOW COLUMNS FROM officers LIKE 'status_reason'")
        if not cursor.fetchone():
            print("[WARN] officers table missing status_reason column! Creating...")
            cursor.execute("ALTER TABLE officers ADD COLUMN status_reason TEXT DEFAULT NULL AFTER status")
            connection.commit()
            print("[OK] status_reason column added to officers")
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
@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

@app.route('/public-view')
def public_view_alias():
    return send_from_directory('.', 'public-display.html')

@app.route('/kiosk-setup')
def kiosk_setup():
    return send_from_directory('.', 'kiosk-setup.html')

@app.route('/download')
def download_page():
    return send_from_directory('.', 'download.html')

@app.route('/api/download/queue-kiosk-setup.exe')
def download_kiosk_installer():
    return send_from_directory(
        'queue-kiosk/dist',
        'QueueKiosk-Setup-1.0.0.exe',
        as_attachment=True,
        mimetype='application/x-msdownload'
    )

@app.route('/api/download/queue-kiosk-student-setup.exe')
def download_student_kiosk_installer():
    return send_from_directory(
        'queue-kiosk-student/dist',
        'QueueKiosk-Student-Setup-1.0.0.exe',
        as_attachment=True,
        mimetype='application/x-msdownload'
    )

@app.route('/api/download/queue-kiosk-index-setup.exe')
def download_index_kiosk_installer():
    return send_from_directory(
        'queue-kiosk-index/dist',
        'QueueKiosk-Index-Setup-1.0.0.exe',
        as_attachment=True,
        mimetype='application/x-msdownload'
    )

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
            AND DATE(requested_at) = CURDATE()
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
        for item in orders:
            cursor.execute("UPDATE offices SET display_order = %s WHERE id = %s", (item['order'], item['id']))
        
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

        cursor.execute("""
            SELECT MAX(
                CAST(SUBSTRING(token_number, LENGTH(%s) + 1) AS UNSIGNED)
            ) AS max_num
            FROM university_tokens
            WHERE office_id = %s
        """, (office['office_code'], office_id))

        result = cursor.fetchone()
        max_number = result['max_num'] or 0

        next_num = max_number + 1
        token_number = f"{office['office_code']}{str(next_num).zfill(2)}"

        print(f"Token generated: {token_number} (max={max_number})")

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
            UPDATE officers SET status='called', current_token=%s, last_activity=NOW()
            WHERE id=%s
        """, (token['token_number'], officer_id))

        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES (%s, %s, 'recall', CONCAT('Called from officer dashboard - Student: ', IFNULL(%s, '')), NOW())
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
            UPDATE officers SET status='called', current_token=%s, last_activity=NOW()
            WHERE id=%s
        """, (token_number, officer_id))

        cursor.execute("""
            INSERT INTO queue_logs (token_number, officer_id, action, action_details, created_at)
            VALUES (%s, %s, 'recall', CONCAT('Called from officer dashboard - Student: ', IFNULL(%s, '')), NOW())
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
            UPDATE officers SET status='busy', last_activity=NOW() 
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
                COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed,
                COUNT(CASE WHEN t.status = 'skipped' THEN 1 END) as skipped
            FROM offices off
            LEFT JOIN university_tokens t ON off.id = t.office_id
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
                  AND DATE(completed_at) = %s
                  AND assigned_officer_id IS NOT NULL
                GROUP BY assigned_officer_id
            ) cnt ON cnt.assigned_officer_id = o.id
            WHERE COALESCE(o.is_admin, 0) = 0
            ORDER BY off.display_order, off.office_name, o.officer_number
        """, (target_date,))
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
    print("=" * 55)
    print("MAKERERE UNIVERSITY QUEUE SYSTEM API")
    print("=" * 55)
    print(f"http://localhost:{PORT}")
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
    print("=" * 55)
    app.run(host='0.0.0.0', port=PORT, debug=True)