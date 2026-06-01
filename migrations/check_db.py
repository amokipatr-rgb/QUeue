import mysql.connector
conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("SELECT token_number, rating, feedback_text, feedback_submitted_at FROM university_tokens WHERE token_number = 'AR01'")
row = cursor.fetchone()
if row:
    print(f'AR01: rating={row[1]}, text="{row[2]}", submitted={row[3]}')

cursor.execute("SELECT token_number, rating, feedback_text, feedback_submitted_at FROM university_tokens WHERE token_number = 'REC11'")
row = cursor.fetchone()
if row:
    print(f'REC11: rating={row[1]}, text="{row[2]}", submitted={row[3]}')

cursor.execute("SELECT token_number, status, rating, feedback_submitted_at FROM university_tokens WHERE feedback_submitted_at IS NOT NULL")
rows = cursor.fetchall()
print(f'\nAll tokens with feedback ({len(rows)}):')
for row in rows:
    print(f'  {row[0]:15s} status={row[1]:12s} rating={row[2]} submitted={row[3]}')

cursor.close()
conn.close()
