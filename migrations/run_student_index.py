import mysql.connector

conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("SHOW INDEX FROM university_tokens WHERE Key_name = 'idx_tokens_student_unrated'")
if cursor.fetchone():
    print('[SKIP] Index already exists')
else:
    cursor.execute("CREATE INDEX idx_tokens_student_unrated ON university_tokens(student_id, status, feedback_submitted_at)")
    conn.commit()
    print('[OK] Index created')

cursor.close()
conn.close()
