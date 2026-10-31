import sqlite3
import pandas as pd
from datetime import datetime

DB_NAME = "maggot_monitoring.db"

def init_db():
    """Menginisialisasi database dan membuat tabel jika belum ada."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS sensor_data (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        suhu REAL NOT NULL,
        kelembapan REAL NOT NULL,
        status_kondisi TEXT NOT NULL,
        status_maggot TEXT NOT NULL,
        rekomendasi TEXT NOT NULL
    );
    """)
    conn.commit()
    conn.close()

def insert_data(suhu, kelembapan, status_kondisi, status_maggot, rekomendasi):
    """Memasukkan data telemetri baru ke database SQLite."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    waktu_sekarang = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute("""
    INSERT INTO sensor_data (timestamp, suhu, kelembapan, status_kondisi, status_maggot, rekomendasi)
    VALUES (?, ?, ?, ?, ?, ?);
    """, (waktu_sekarang, suhu, kelembapan, status_kondisi, status_maggot, rekomendasi))
    conn.commit()
    conn.close()

def get_historical_data(limit=1000):
    """Mengambil data historis terbaru dalam bentuk Pandas DataFrame."""
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT timestamp as Waktu, suhu as 'Suhu (°C)', kelembapan as 'Kelembaban (%)', 
           status_kondisi as 'Status Kondisi', status_maggot as 'Status Maggot', 
           rekomendasi as Rekomendasi 
    FROM sensor_data 
    ORDER BY id DESC 
    LIMIT ?;
    """
    df = pd.read_sql_query(query, conn, params=(limit,))
    conn.close()
    return df

def get_all_data():
    """Mengambil seluruh data untuk diekspor ke Excel / CSV."""
    conn = sqlite3.connect(DB_NAME)
    query = """
    SELECT id as ID, timestamp as Waktu, suhu as 'Suhu (°C)', kelembapan as 'Kelembaban (%)', 
           status_kondisi as 'Status Kondisi', status_maggot as 'Status Maggot', 
           rekomendasi as Rekomendasi 
    FROM sensor_data 
    ORDER BY id DESC;
    """
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def get_analytics_summary():
    """Mengambil summary statistik dari database."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Total Data, Rata-rata Suhu, Rata-rata Kelembaban
    cursor.execute("SELECT COUNT(*), AVG(suhu), AVG(kelembapan) FROM sensor_data")
    count, avg_temp, avg_hum = cursor.fetchone()
    
    # 2. Distribusi Status Maggot
    cursor.execute("SELECT status_maggot, COUNT(*) FROM sensor_data GROUP BY status_maggot")
    distribution = dict(cursor.fetchall())
    
    conn.close()
    
    return {
        "total_data": count if count else 0,
        "avg_temp": round(avg_temp, 2) if avg_temp else 0.0,
        "avg_hum": round(avg_hum, 2) if avg_hum else 0.0,
        "distribution": distribution
    }
