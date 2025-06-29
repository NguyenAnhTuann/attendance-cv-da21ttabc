import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict
import os
import re
import unicodedata
from datetime import datetime

# Hàm chuẩn hóa tên môn học thành tên file không dấu, viết thường, không khoảng trắng
def to_filename(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'\s+', '', text)  # xóa khoảng trắng
    return text.lower()

mssv = input("Nhập MSSV: ").strip()

conn = sqlite3.connect('../db/attendance.db')
cursor = conn.cursor()

cursor.execute("SELECT hoten FROM sinhvien WHERE mssv = ?", (mssv,))
res = cursor.fetchone()
if not res:
    print("❌ Không tìm thấy MSSV.")
    exit()
hoten = res[0]

# Lấy danh sách môn học mà sinh viên đã học
cursor.execute("SELECT DISTINCT monhoc FROM diemdanh WHERE mssv = ?", (mssv,))
mon_list = [row[0] for row in cursor.fetchall()]
if not mon_list:
    print("❌ Sinh viên này chưa có dữ liệu điểm danh.")
    exit()

# Hiển thị danh sách môn học để chọn
print("📚 Danh sách môn học đã học:")
for i, mon in enumerate(mon_list, 1):
    print(f"{i}. {mon}")

chon = input("👉 Nhập số thứ tự môn học cần thống kê: ").strip()
if not chon.isdigit() or int(chon) < 1 or int(chon) > len(mon_list):
    print("❌ Lựa chọn không hợp lệ.")
    exit()

monhoc = mon_list[int(chon) - 1]
monhoc_filename = to_filename(monhoc)

# Lấy điểm danh theo môn đã chọn
cursor.execute("""
    SELECT ngayhoc
    FROM diemdanh
    WHERE mssv = ? AND monhoc = ?
    ORDER BY ngayhoc
""", (mssv, monhoc))
rows = cursor.fetchall()
conn.close()

if not rows:
    print("❌ Không có dữ liệu điểm danh cho môn học đã chọn.")
    exit()

# Gom số lần điểm danh theo từng ngày sau khi chuẩn hóa định dạng ngày
ngay_data = defaultdict(int)
for ngay, in rows:
    try:
        # Chuẩn hóa: loại bỏ khoảng trắng và định dạng dd/mm/yyyy
        ngay = datetime.strptime(ngay.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")
        ngay_data[ngay] += 1
    except ValueError:
        print(f"⚠️ Ngày không hợp lệ bị bỏ qua: {ngay}")

# Xác định tên file & xóa nếu đã tồn tại
output_file = f"thongke/thongke.{mssv}.{monhoc_filename}.xlsx"
if os.path.exists(output_file):
    os.remove(output_file)
    print("🗑️ Đã xóa file cũ trùng tên.")

# Ghi file Excel
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    workbook = writer.book
    ngay_sorted = sorted(ngay_data.items())

    df = pd.DataFrame({
        "STT": range(1, len(ngay_sorted) + 1),
        "Ngày học (dd/mm/yyyy)": [ngay for ngay, _ in ngay_sorted],
        "Số lần điểm danh": [solan for _, solan in ngay_sorted]
    })

    sheet_name = "ThongKe"
    df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=5)

    worksheet = writer.sheets[sheet_name]
    worksheet.write("A1", f"Họ tên: {hoten}")
    worksheet.write("A2", f"MSSV: {mssv}")
    worksheet.write("A3", f"Môn học: {monhoc}")
    worksheet.write("A4", f"Số buổi học: {len(ngay_sorted)}")

    # Vẽ biểu đồ
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
        'name': monhoc,
        'categories': f"='{sheet_name}'!$A$6:$A${len(df)+5}",
        'values':     f"='{sheet_name}'!$C$6:$C${len(df)+5}",
    })
    chart.set_title({'name': f"Biểu đồ điểm danh - {monhoc}"})
    chart.set_x_axis({'name': 'STT'})
    chart.set_y_axis({'name': 'Số lần', 'major_unit': 1})

    worksheet.insert_chart('E2', chart)

print(f"✅ Đã xuất thống kê môn {monhoc} cho sinh viên {hoten}: {output_file}")
