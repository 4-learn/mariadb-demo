import mariadb

try:
    conn = mariadb.connect(
        user="project_user",
        password="YourPass123",
        host="localhost",
        database="your_database"
    )
    cursor = conn.cursor()

    # 刪除員工資料
    cursor.execute("DELETE FROM employees WHERE name = 'Michael Brown'")
    conn.commit()
    print("Employee deleted successfully!")

except mariadb.Error as e:
    print(f"Error deleting data: {e}")

finally:
    if conn:
        conn.close()
