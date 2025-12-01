import sqlite3
import time
from datetime import datetime

# Assuming you have a function to read sensor data
def read_humidity():
    # Replace with your actual sensor reading code
    return 60.2 # Example humidity

conn = sqlite3.connect('sensor_data.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS readings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        humidity REAL
    )
''')
conn.commit()

while True:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    humidity = read_humidity()
    cursor.execute("INSERT INTO readings (timestamp, humidity) VALUES (?, ?)", (timestamp, humidity))
    conn.commit()
    time.sleep(5)