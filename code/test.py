import psycopg2

try:
    # Connect without providing a password
    conn = psycopg2.connect(
        dbname="postgres",
        user="root",
        host="/var/run/postgresql",  # Default location for Unix socket
        port=5432
    )
    print("Connected to PostgreSQL!")
    conn.close()
except Exception as e:
    print("Error connecting to PostgreSQL:", e)