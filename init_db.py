import pyodbc

# SQL Server configuration
server = 'DESKTOP-Q664GNP\\SQLEXPRESS'
database = 'trade-order'
driver = '{ODBC Driver 11 for SQL Server}'

# Step 1: Connect to SQL Server (without DB) to create the DB if needed
conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};Trusted_Connection=yes;')
conn.autocommit = True
cursor = conn.cursor()

cursor.execute(f"IF DB_ID('{database}') IS NULL CREATE DATABASE [{database}]")
print(f"✅ Database '{database}' ensured.")
conn.close()

# Step 2: Connect to the database
conn = pyodbc.connect(f'DRIVER={driver};SERVER={server};DATABASE={database};Trusted_Connection=yes;')
cursor = conn.cursor()

# Step 3: Read and execute schema.sql
with open("schema.sql", "r", encoding="utf-8") as file:
    sql_script = file.read()

# Step 4: Split and execute each statement
for stmt in sql_script.strip().split(';'):
    if stmt.strip():
        try:
            cursor.execute(stmt)
            print(f"✅ Executed: {stmt.strip().splitlines()[0]}")
        except Exception as e:
            print(f"❌ Error in: {stmt.strip().splitlines()[0]}")
            print(e)

conn.commit()
conn.close()
print("✅ Database schema and sample data initialized successfully.")
