import mysql.connector

conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("""
    SELECT o.office_name, s.id 
    FROM services s 
    JOIN offices o ON s.office_id = o.id 
    WHERE s.service_code = 'PS' 
    ORDER BY o.id, s.id
""")
rows = cursor.fetchall()

print('PS services found:')
seen = set()
to_delete = []
for r in rows:
    print(f'  office={r[0]:35s} id={r[1]}')
    if r[0] in seen:
        to_delete.append(r[1])
    else:
        seen.add(r[0])

if to_delete:
    placeholders = ','.join(['%s'] * len(to_delete))
    cursor.execute(f"DELETE FROM services WHERE id IN ({placeholders})", to_delete)
    conn.commit()
    print(f'Deleted {len(to_delete)} duplicate(s): {to_delete}')
else:
    print('No duplicates')

cursor.close()
conn.close()
