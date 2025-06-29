import pandas as pd
import sqlite3
from datetime import datetime
import os
import unicodedata
import re

def to_filename(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')  # Xoá dấu
    text = re.sub(r'\s+', '', text)  # Xoá khoảng trắng
    return text.lower()


def thongke_diemdanh_lop_theo_ngay():
    # Kết nối cơ sở dữ liệu
    conn = sqlite3.connect('../db/attendance.db')
    cursor = conn.cursor()

    # Hiển thị danh sách file trong thư mục
    folder_path = "data-da21ttabc"
    files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]

    if not files:
        print("❌ Không tìm thấy file Excel trong thư mục.")
        return

    print("\n📂 Chọn danh sách lớp:")
    for i, file in enumerate(files, 1):
        print(f"{i}. {file}")

    try:
        chon = int(input("Nhập số: ").strip())
        file_path = os.path.join(folder_path, files[chon - 1])
    except (ValueError, IndexError):
        print("❌ Lựa chọn không hợp lệ.")
        return

    # Đọc danh sách lớp
    df = pd.read_excel(file_path)
    danh_sach_mssv = df["MSSV"].astype(str).tolist()

    # Lấy danh sách môn học liên quan đến lớp này
    placeholders = ','.join('?' for _ in danh_sach_mssv)
    cursor.execute(f"SELECT DISTINCT monhoc FROM diemdanh WHERE mssv IN ({placeholders})", danh_sach_mssv)
    mon_list = [row[0] for row in cursor.fetchall()]

    if not mon_list:
        print("❌ Không tìm thấy môn học nào liên quan đến lớp này.")
        return

    print("\n📚 Chọn môn học:")
    for i, mon in enumerate(mon_list, 1):
        print(f"{i}. {mon}")
    try:
        monchon = int(input("Nhập số: ").strip())
        monhoc = mon_list[monchon - 1]
    except (ValueError, IndexError):
        print("❌ Lựa chọn không hợp lệ.")
        return

    # Nhập ngày học cần thống kê
    ngayhoc_raw = input("📅 Nhập ngày cần thống kê (dd/mm/yyyy): ").strip()
    try:
        ngayhoc = datetime.strptime(ngayhoc_raw, "%d/%m/%Y").strftime("%d/%m/%Y")
    except:
        print("❌ Ngày không hợp lệ.")
        return

    # Tạo cột trạng thái điểm danh
    trangthai = []
    tong_hien_dien = 0
    for mssv in danh_sach_mssv:
        cursor.execute("SELECT 1 FROM diemdanh WHERE mssv = ? AND ngayhoc = ? AND monhoc = ?", (mssv, ngayhoc, monhoc))
        if cursor.fetchone():
            trangthai.append("✓")
            tong_hien_dien += 1
        else:
            trangthai.append("x")

    # Gán cột mới vào DataFrame
    df["Trạng thái điểm danh"] = trangthai

    # ===== Ghi file Excel =====
    output_dir = "thongke_tungngay"
    os.makedirs(output_dir, exist_ok=True)

    safe_monhoc = to_filename(monhoc)
    filename = f"diemdanh_{safe_monhoc}_{ngayhoc.replace('/', '-')}.xlsx"
    output_file = os.path.join(output_dir, filename)

    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name="Sheet1")

        workbook = writer.book
        worksheet = writer.sheets['Sheet1']

        # Định dạng màu vàng
        format_yellow = workbook.add_format({
            'bg_color': '#FFF200',
            'bold': True,
            'border': 1
        })

        # Ghi tổng hiện diện + tổng vắng vào cuối file (sau cùng)
        last_row = len(df) + 1  # +1 để không đè lên sinh viên cuối
        worksheet.write(last_row, 4, "Tổng hiện diện:", format_yellow)
        worksheet.write(last_row, 5, tong_hien_dien, format_yellow)
        worksheet.write(last_row + 1, 4, "Tổng vắng:", format_yellow)
        worksheet.write(last_row + 1, 5, len(danh_sach_mssv) - tong_hien_dien, format_yellow)

    print(f"✅ Xuất file thống kê: {output_file}")
    conn.close()

if __name__ == "__main__":
    thongke_diemdanh_lop_theo_ngay()
