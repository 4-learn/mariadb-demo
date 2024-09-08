import mariadb

try:
    conn = mariadb.connect(
        user="project_user",
        password="YourPass123",
        host="localhost",
        database="your_database"
    )
    cursor = conn.cursor()

    # 查詢資料（R：Read）
    cursor.execute("SELECT * FROM employees")
    for row in cursor:
        print(f"ID: {row[0]}, Name: {row[1]}, Position: {row[2]}, Salary: {row[3]}, Hire Date: {row[4]}")

except mariadb.Error as e:
    print(f"Error connecting to MariaDB: {e}")

finally:
    if conn:
        conn.close()
