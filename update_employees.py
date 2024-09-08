import mariadb

try:
    conn = mariadb.connect(
        user="project_user",
        password="YourPass123",
        host="localhost",
        database="your_database"
    )
    cursor = conn.cursor()

    # 更新員工薪水
    cursor.execute("UPDATE employees SET salary = 85000 WHERE name = 'Michael Brown'")
    conn.commit()
    print("Employee salary updated successfully!")

except mariadb.Error as e:
    print(f"Error updating data: {e}")

finally:
    if conn:
        conn.close()
