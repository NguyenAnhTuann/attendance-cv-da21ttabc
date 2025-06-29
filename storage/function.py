import sqlite3
from datetime import datetime


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
    malop = input("Nhập Mã lớp: ")
    ngaysinh = input("Nhập ngày sinh (YYYY-MM-DD): ")
    gioitinh = input("Nhập giới tính: ")
    ngaytao = datetime.now().strftime('%d/%m/%Y')
    solantruycap = 0

    cursor.execute('''
        INSERT INTO sinhvien (mssv, hoten, malop, ngaysinh, gioitinh, ngaytao, solantruycap)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    ''', (mssv, hoten, malop, ngaysinh, gioitinh, ngaytao, solantruycap))
    conn.commit()
    print("✅ Đã thêm sinh viên.")

def suasinhvien():
    mssv = input("Nhập MSSV cần sửa: ")
    hoten_moi = input("Nhập tên mới: ")
    cursor.execute("UPDATE sinhvien SET hoten = ? WHERE mssv = ?", (hoten_moi, mssv))
    conn.commit()
    print("✅ Đã sửa thông tin sinh viên.")

def xoasinhvien():
    mssv = input("Nhập MSSV cần xóa: ")
    cursor.execute("DELETE FROM sinhvien WHERE mssv = ?", (mssv,))
    conn.commit()
    print("✅ Đã xóa sinh viên.")

def hienthidiemdanh():
    cursor.execute("SELECT * FROM diemdanh")
    rows = cursor.fetchall()
    for row in rows:
        print(row)

def themdiemdanh():
    mssv = input("Nhập MSSV điểm danh: ")
    thoigian = input("Nhập thời gian (HH:MM:SS): ")
    ngayhoc_raw = input("Nhập ngày học (dd/mm/yyyy): ")
    try:
        ngayhoc = datetime.strptime(ngayhoc_raw.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")
    except ValueError:
        print("❌ Định dạng ngày không hợp lệ. Vui lòng nhập đúng dd/mm/yyyy.")
        return
    monhoc = input("Nhập môn học: ")
    trangthai = input("Nhập trạng thái vào lớp: ")

    cursor.execute('''
        INSERT INTO diemdanh (mssv, thoigian, ngayhoc, monhoc, trangthaivaolop)
        VALUES (?, ?, ?, ?, ?)
    ''', (mssv, thoigian, ngayhoc, monhoc, trangthai))
    conn.commit()
    print("✅ Đã điểm danh.")

def xoadiemdanh():
    mssv = input("Nhập MSSV cần xóa điểm danh: ")
    ngayhoc_raw = input("Nhập ngày học (dd/mm/yyyy): ")
    monhoc = input("Nhập môn học: ")

    try:
        ngayhoc = datetime.strptime(ngayhoc_raw.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")
    except ValueError:
        print("❌ Định dạng ngày không hợp lệ. Vui lòng nhập đúng dd/mm/yyyy.")
        return

    cursor.execute("DELETE FROM diemdanh WHERE mssv = ? AND ngayhoc = ? AND monhoc = ?", (mssv, ngayhoc, monhoc))
    conn.commit()
    print("✅ Đã xóa điểm danh.")

# --- Menu ---
while True:
    print("\n--- MENU ---")
    print("1. Thêm sinh viên")
    print("2. Hiển thị sinh viên")
    print("3. Sửa sinh viên")
    print("4. Xóa sinh viên")
    print("5. Thêm điểm danh")
    print("6. Hiển thị điểm danh")
    print("7. Xóa điểm danh")
    print("8. Thống kê số buổi học của sinh viên")
    print("9. Thống kê điểm danh lớp theo ngày")
    print("10. Thống kê điểm danh nhiều ngày")
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
    elif choice == '8':
        import thongke
    elif choice == '9':
        from thongke_tungngay import thongke_diemdanh_lop_theo_ngay
        thongke_diemdanh_lop_theo_ngay()
    elif choice == '10':
        from thongke_nhieungay import main
        main()
    elif choice == '0':
        print("👋 Thoát chương trình.")
        break
    else:
        print("⚠ Lựa chọn không hợp lệ.")

conn.close()
