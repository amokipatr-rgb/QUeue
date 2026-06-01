import mysql.connector

conn = mysql.connector.connect(host='localhost', port=3306, user='root', password='', database='db')
cursor = conn.cursor()

cursor.execute("SELECT id, office_name FROM offices ORDER BY id")
offices = cursor.fetchall()

# Change unique constraint from global service_code to per-office (office_id, service_code)
cursor.execute("SHOW INDEX FROM services WHERE Key_name = 'service_code'")
if cursor.fetchone():
    cursor.execute("ALTER TABLE services DROP INDEX service_code")
    cursor.execute("ALTER TABLE services ADD UNIQUE KEY unique_service_per_office (office_id, service_code)")
    conn.commit()
    print('[OK] Changed unique constraint to per-office (office_id, service_code)')

cursor.execute("SELECT office_id, id FROM services WHERE service_code = 'PS'")
existing = {row[0] for row in cursor.fetchall()}
# Show existing PS entries
cursor.execute("SELECT id, office_id, service_code, service_name FROM services WHERE service_code = 'PS'")
print('Existing PS services:')
for r in cursor.fetchall():
    print(f'  id={r[0]} office={r[1]} code={r[2]} name={r[3]}')
# Check unique constraints
cursor.execute("SHOW CREATE TABLE services")
create = cursor.fetchone()[1]
print()
print('Services table constraints:')
for line in create.split(','):
    if 'UNIQUE' in line.upper():
        print(f'  {line.strip()}')

added = 0
for office in offices:
    oid, oname = office
    if oid not in existing:
        cursor.execute("""
            SELECT COALESCE(MAX(display_order), 0) + 1 FROM services WHERE office_id = %s
        """, (oid,))
        next_order = cursor.fetchone()[0]
        cursor.execute("""
            INSERT INTO services (service_code, service_name, office_id, description, estimated_time_minutes, display_order, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, 1)
        """, ('PS', 'Parent Interaction', oid, 'Priority service for parents and visitors', 5, next_order))
        added += 1
        print(f'[OK] Added PS service to {oname}')
    else:
        print(f'[SKIP] PS already exists for {oname}')

conn.commit()
cursor.close()
conn.close()
print(f'Done. Added {added} PS service(s).')
