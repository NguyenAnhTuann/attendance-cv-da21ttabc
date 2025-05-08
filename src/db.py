import sqlite3
import os

if not os.path.exists('../db'):
    os.makedirs('../db')

# kết nối db
conn = sqlite3.connect('../db/attendance.db')
cursor = conn.cursor()

#  bảng snh viên
cursor.execute('''
CREATE TABLE IF NOT EXISTS sinhvien (
    ma_sv TEXT PRIMARY KEY,
    ho_ten TEXT
)
''')

# bảng điểm danh
cursor.execute('''
CREATE TABLE IF NOT EXISTS diemdanh (
    ma_sv TEXT,
    ngay_hoc DATE,
    FOREIGN KEY(ma_sv) REFERENCES sinhvien(ma_sv)
)
''')

conn.commit()
conn.close()

print("Database và bảng đã được tạo thành công!")
