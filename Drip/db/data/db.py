import sqlite3

conn = sqlite3.connect("riego.db")
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
print(cursor.fetchall())


cursor.execute("SELECT * FROM parcelas")
rows = cursor.fetchall()

for row in rows:
    print(row)


tables = ['parcelas', 'clima_diario', 'lecturas_sensor',
          'eventos_riego', 'log_decisiones', 'erp_costos']

for table in tables:
    print(f"\n--- {table} ---")

    cursor.execute(f"SELECT * FROM {table} LIMIT 5")
    
    for row in cursor.fetchall():
        print(row)