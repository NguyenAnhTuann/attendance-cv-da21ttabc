import sqlite3

conn = sqlite3.connect('../db/attendance.db')
cursor = conn.cursor()

def hienthisinhvien():
    cursor.execute("SELECT * FROM sinhvien")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def themsinhvien():
    mssv = input("Nhập MSSV: ")
    hoten = input("Nhập Họ Tên: ")
    cursor.execute("INSERT INTO sinhvien (mssv, hoten) VALUES (?, ?)", (mssv, hoten))
    conn.commit()
    print("Đã thêm sinh viên.")

def suasinhvien():
    mssv = input("Nhập MSSV cần sửa: ")
    hoten_moi = input("Nhập tên mới: ")
    cursor.execute("UPDATE sinhvien SET hoten = ? WHERE mssv = ?", (hoten_moi, mssv))
    conn.commit()
    print("Đã sửa.")

def xoasinhvien():
    mssv = input("Nhập MSSV cần xóa: ")
    cursor.execute("DELETE FROM sinhvien WHERE mssv = ?", (mssv,))
    conn.commit()
    print("Đã xóa.")

def hienthidiemdanh():
    cursor.execute("SELECT * FROM diemdanh")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def themdiemdanh():
    mssv = input("Nhập MSSV điểm danh: ")
    ngayhoc = input("Nhập ngày học (YYYY-MM-DD): ")
    cursor.execute("INSERT INTO diemdanh (mssv, ngayhoc) VALUES (?, ?)", (mssv, ngayhoc))
    conn.commit()
    print("Đã điểm danh.")

def xoadiemdanh():
    mssv = input("Nhập MSSV cần xóa điểm danh: ")
    ngayhoc = input("Nhập ngày học (YYYY-MM-DD): ")
    cursor.execute("DELETE FROM diemdanh WHERE mssv = ? AND ngayhoc = ?", (mssv, ngayhoc))
    conn.commit()
    print("Đã xóa điểm danh.")

while True:
    print("\n--- MENU ---")
    print("1. Thêm sinh viên")
    print("2. Hiển thị sinh viên")
    print("3. Sửa sinh viên")
    print("4. Xóa sinh viên")
    print("5. Thêm điểm danh")
    print("6. Hiển thị điểm danh")
    print("7. Xóa điểm danh")
    print("0. Thoát")

    choice = input("Chọn thao tác: ")

    if choice == '1':
        themsinhvien()
    elif choice == '2':
        hienthisinhvien()
    elif choice == '3':
        suasinhvien()
    elif choice == '4':
        xoasinhvien()
    elif choice == '5':
        themdiemdanh()
    elif choice == '6':
        hienthidiemdanh()
    elif choice == '7':
        xoadiemdanh()
    elif choice == '0':
        print("Thoát chương trình.")
        break
    else:
        print("Lựa chọn không hợp lệ.")

conn.close()
