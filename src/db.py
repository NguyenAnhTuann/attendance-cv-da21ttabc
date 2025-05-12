import sqlite3
import os

if not os.path.exists('../db'):
    os.makedirs('../db')

# kết nối db
conn = sqlite3.connect('../db/attendance.db')
cursor = conn.cursor()

# bảng sinhvien
cursor.execute('''
CREATE TABLE IF NOT EXISTS sinhvien (
    mssv TEXT PRIMARY KEY,
    hoten TEXT,
    malop TEXT,
    ngaysinh TEXT,
    gioitinh TEXT,
    ngaytao DATE,
    solantruycap INTEGER
)
''')



# bảng điểm danh
cursor.execute('''
CREATE TABLE IF NOT EXISTS diemdanh (
    mssv TEXT,
    ngayhoc DATE,
    monhoc TEXT,
    FOREIGN KEY(mssv) REFERENCES sinhvien(mssv)
)
''')

conn.commit()
conn.close()

print("Database và bảng đã được tạo thành công!")
