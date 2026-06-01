import pymysql
conn = pymysql.connect(host='localhost', user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("SHOW COLUMNS FROM university_tokens LIKE 'parent_name'")
if cursor.fetchone():
    print('Columns already exist, skipping')
else:
    cursor.execute("ALTER TABLE university_tokens ADD COLUMN parent_name VARCHAR(100) DEFAULT NULL AFTER student_phone")
    cursor.execute("ALTER TABLE university_tokens ADD COLUMN parent_phone VARCHAR(20) DEFAULT NULL AFTER parent_name")
    cursor.execute("ALTER TABLE university_tokens ADD COLUMN is_priority TINYINT(1) DEFAULT 0 AFTER parent_phone")
    cursor.execute("ALTER TABLE university_tokens ADD INDEX idx_priority (is_priority, office_id, status)")
    conn.commit()
    print('Migration completed')
cursor.close()
conn.close()
