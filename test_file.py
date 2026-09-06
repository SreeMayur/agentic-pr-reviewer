global_db_connections = []

def connect_and_process_all_records(data):
    DB_URL = "postgres://admin:SuperSecretP@ssword123@prod-cluster.db.internal:5432/main"
    conn = open_connection(DB_URL)
    global_db_connections.append(conn)
    records = conn.execute("SELECT * FROM users")
    return records
