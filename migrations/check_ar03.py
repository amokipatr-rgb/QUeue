import mysql.connector
conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("SELECT token_number, status, rating, feedback_text, feedback_submitted_at FROM university_tokens WHERE token_number = 'AR03'")
row = cursor.fetchone()
if row:
    print(f'Token: {row[0]}')
    print(f'Status: {row[1]}')
    print(f'Rating: {row[2]}')
    print(f'Text: "{row[3]}"')
    print(f'Submitted: {row[4]}')
cursor.close()
conn.close()
