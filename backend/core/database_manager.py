"""
Database Manager for CRUD operations
"""
from app.moduls.payment import payment_manager

def update_database_record(table_name, row_id, column, value):
    """Update record in database"""
    try:
        # Thực hiện update trực tiếp
        conn = payment_manager._get_connection()
        cursor = conn.cursor()

        # Xử lý kiểu dữ liệu cho value
        if isinstance(value, str) and not value:
            value = None  # Empty string -> NULL

        # Validate table and column exist
        cursor.execute("PRAGMA table_info(" + table_name + ")")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        if column not in column_names:
            conn.close()
            return False, f'Column {column} does not exist in table {table_name}'

        # Thực hiện update
        cursor.execute(f"UPDATE {table_name} SET {column} = ? WHERE id = ?", (value, row_id))

        if cursor.rowcount == 0:
            conn.close()
            return False, f'No row found with id {row_id} in table {table_name}'

        conn.commit()
        conn.close()

        return True, f'Updated {table_name}.{column} successfully'

    except Exception as e:
        print(f"Update error: {str(e)}")
        return False, str(e)

def add_database_record(table_name, row_data):
    """Add new record to database"""
    try:
        # Validate table exists
        conn = payment_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute("PRAGMA table_info(" + table_name + ")")
        columns = cursor.fetchall()
        column_names = [col[1] for col in columns]

        # Filter out invalid columns and build insert query
        valid_data = {}
        for col, value in row_data.items():
            if col in column_names and col != 'id':  # Skip id column (auto-increment)
                valid_data[col] = value

        if not valid_data:
            conn.close()
            return False, 'No valid columns to insert'

        # Build INSERT query
        columns_str = ', '.join(valid_data.keys())
        placeholders = ', '.join(['?' for _ in valid_data])
        values = list(valid_data.values())

        query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
        cursor.execute(query, values)

        new_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return True, f'Added to {table_name} successfully', new_id

    except Exception as e:
        print(f"Add error: {str(e)}")
        return False, str(e), None

def delete_database_record(table_name, row_id):
    """Delete record from database"""
    try:
        # Thực hiện delete
        conn = payment_manager._get_connection()
        cursor = conn.cursor()

        cursor.execute(f"DELETE FROM {table_name} WHERE id = ?", (row_id,))

        if cursor.rowcount == 0:
            conn.close()
            return False, f'No row found with id {row_id} in table {table_name}'

        conn.commit()
        conn.close()

        return True, f'Deleted from {table_name} successfully'

    except Exception as e:
        print(f"Delete error: {str(e)}")
        return False, str(e)
