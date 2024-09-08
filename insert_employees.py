import mariadb

try:
    conn = mariadb.connect(
        user="project_user",
        password="YourPass123",
        host="localhost",
        database="your_database"
    )
    cursor = conn.cursor()

    # 插入新員工資料
    cursor.execute("INSERT INTO employees (id, name, position, salary, hire_date) VALUES (6, 'Michael Brown', 'DevOps Engineer', 80000.00, '2023-03-10')")
    conn.commit()
    print("Employee added successfully!")

except mariadb.Error as e:
    print(f"Error inserting data: {e}")

finally:
    if conn:
        conn.close()
