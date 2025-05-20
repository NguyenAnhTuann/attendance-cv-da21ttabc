import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Nhập MSSV
mssv = input("Nhập MSSV: ").strip()

# Kết nối DB
conn = sqlite3.connect('../db/attendance.db')
cursor = conn.cursor()

# Lấy họ tên
cursor.execute("SELECT hoten FROM sinhvien WHERE mssv = ?", (mssv,))
res = cursor.fetchone()
if not res:
    print("❌ Không tìm thấy MSSV.")
    exit()
hoten = res[0]

# Lấy dữ liệu điểm danh có môn học
cursor.execute("""
    SELECT ngayhoc, monhoc
    FROM diemdanh
    WHERE mssv = ?
    ORDER BY ngayhoc
""", (mssv,))
rows = cursor.fetchall()
conn.close()

# Xử lý thống kê
data_dict = defaultdict(lambda: defaultdict(int))  # data_dict[monhoc][ngay] = count
for ngay, monhoc in rows:
    data_dict[monhoc][ngay] += 1

# Ghi vào Excel
output_file = f"thongke.{mssv}.xlsx"
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    workbook  = writer.book

    worksheet_index = 0
    for monhoc, ngay_data in data_dict.items():
        # Chuyển đổi ngày sang thứ tự ngày học: 1, 2, 3...
        ngay_sorted = sorted(ngay_data.keys())
        ngay_mapping = {ngay: idx + 1 for idx, ngay in enumerate(ngay_sorted)}
        df = pd.DataFrame({
            "Ngày học (STT)": [ngay_mapping[ngay] for ngay in ngay_data.keys()],
            "Ngày học (dd/mm/yyyy)": list(ngay_data.keys()),
            "Số lần điểm danh": pd.Series(ngay_data.values(), dtype=int)
        })

        sheet_name = f"Môn{worksheet_index+1}"
        df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=5)

        worksheet = writer.sheets[sheet_name]
        worksheet.write("A1", f"Họ tên: {hoten}")
        worksheet.write("A2", f"MSSV: {mssv}")
        worksheet.write("A3", f"Môn học: {monhoc}")
        worksheet.write("A4", f"Số buổi học: {sum(ngay_data.values())}")

        # Vẽ biểu đồ
        chart = workbook.add_chart({'type': 'column'})
        chart.add_series({
            'name': f"{monhoc}",
            'categories': f"='{sheet_name}'!$A$6:$A${len(df)+5}",
            'values':     f"='{sheet_name}'!$C$6:$C${len(df)+5}",
        })
        chart.set_title({'name': f"Biểu đồ điểm danh - {monhoc}"})
        chart.set_x_axis({'name': 'Thứ tự buổi học'})
        chart.set_y_axis({
        'name': 'Số lần',
        'major_unit': 1
        })

        worksheet.insert_chart('E2', chart)
        worksheet_index += 1

print(f"✅ Đã xuất thống kê chi tiết ra file: {output_file}")
