import pandas as pd
import sqlite3
from datetime import datetime
from tkinter import filedialog, Tk
import os

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

    print("\n📚 Chọn danh sách lớp:")
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
    ngayhoc_raw = input("📅 Nhập ngày cần thống kê (dd/mm/yyyy): ").strip()
    try:
        ngayhoc = datetime.strptime(ngayhoc_raw, "%d/%m/%Y").strftime("%d/%m/%Y")
    except:
        print("❌ Ngày không hợp lệ.")
        return

    danh_sach_mssv = df["MSSV"].astype(str).tolist()

    # Tạo cột trạng thái
    trangthai = []
    tong_hien_dien = 0
    for mssv in danh_sach_mssv:
        cursor.execute("SELECT 1 FROM diemdanh WHERE mssv = ? AND ngayhoc = ?", (mssv, ngayhoc))
        if cursor.fetchone():
            trangthai.append("✓")
            tong_hien_dien += 1
        else:
            trangthai.append("x")

    # Thêm cột trạng thái vào DataFrame
    df["Trạng thái điểm danh"] = trangthai
    df.loc[len(df.index), "Tên lớp"] = "Tổng hiện diện:"
    df.loc[len(df.index)-1, "Trạng thái điểm danh"] = tong_hien_dien
    df.loc[len(df.index), "Tên lớp"] = "Tổng vắng:"
    df.loc[len(df.index)-1, "Trạng thái điểm danh"] = len(danh_sach_mssv) - tong_hien_dien

    # Xuất file Excel
    output_dir = "thongke_tungngay"
    os.makedirs(output_dir, exist_ok=True)  # Tạo thư mục nếu chưa có

    filename = f"diemdanh_{ngayhoc.replace('/', '-')}.xlsx"
    output_file = os.path.join(output_dir, filename)
    with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False)
    workbook = writer.book
    worksheet = writer.sheets['Sheet1']

    # Định dạng màu vàng
    format_yellow = workbook.add_format({
        'bg_color': '#FFF200',  # màu vàng
        'bold': True,
        'border': 1
    })

    # Xác định vị trí 4 ô cuối (dòng, cột)
    last_row = len(df)
    worksheet.write(last_row - 2, 4, "Tổng hiện diện:", format_yellow)  # Cột E = index 4
    worksheet.write(last_row - 2, 5, tong_hien_dien, format_yellow)     # Cột F = index 5
    worksheet.write(last_row - 1, 4, "Tổng vắng:", format_yellow)
    worksheet.write(last_row - 1, 5, len(danh_sach_mssv) - tong_hien_dien, format_yellow)
    print(f"✅ Xuất file thống kê: {output_file}")

    conn.close()
