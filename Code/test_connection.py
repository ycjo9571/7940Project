import psycopg2

# Connection parameters (update with your credentials)
conn_params = {
    'dbname': 'chatbot',
    'user': 'ychwu',
    'password': '19957112johnWU',
    'host': 'localhost',
    'port': '5432'
}

try:
    # Establish a connection
    conn = psycopg2.connect(**conn_params)
    print("Connected to PostgreSQL database!")

    # Create a cursor to execute SQL commands
    cursor = conn.cursor()

    # Example: Execute a simple query
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print("PostgreSQL Version:", version)

except psycopg2.OperationalError as e:
    print(f"Connection failed: {e}")
finally:
    # Close cursor and connection
    if 'cursor' in locals():
        cursor.close()
    if 'conn' in locals():
        conn.close()
        print("Connection closed.")
