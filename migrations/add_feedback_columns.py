import mysql.connector
conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("SHOW COLUMNS FROM university_tokens LIKE 'rating'")
if not cursor.fetchone():
    cursor.execute("ALTER TABLE university_tokens ADD COLUMN rating TINYINT DEFAULT NULL COMMENT '1-5 star rating' AFTER call_attempts")
    print('Added rating column')

cursor.execute("SHOW COLUMNS FROM university_tokens LIKE 'feedback_text'")
if not cursor.fetchone():
    cursor.execute("ALTER TABLE university_tokens ADD COLUMN feedback_text TEXT DEFAULT NULL COMMENT 'Optional written feedback' AFTER rating")
    print('Added feedback_text column')

cursor.execute("SHOW COLUMNS FROM university_tokens LIKE 'feedback_submitted_at'")
if not cursor.fetchone():
    cursor.execute("ALTER TABLE university_tokens ADD COLUMN feedback_submitted_at TIMESTAMP NULL DEFAULT NULL COMMENT 'When feedback was given' AFTER feedback_text")
    print('Added feedback_submitted_at column')

conn.commit()
cursor.close()
conn.close()
print('Migration complete')
