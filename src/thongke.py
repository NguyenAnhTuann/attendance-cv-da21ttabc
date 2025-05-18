import sqlite3
import pandas as pd
import matplotlib.pyplot as plt
from collections import defaultdict

# Nhập MSSV
mssv = input("Nhập MSSV: ").strip()

# Kết nối DB
conn = sqlite3.connect('../db/attendance.db')
cursor = conn.cursor()

cursor.execute("SELECT hoten FROM sinhvien WHERE mssv = ?", (mssv,))
res = cursor.fetchone()
if not res:
    print("❌ Không tìm thấy MSSV.")
    exit()
hoten = res[0]

cursor.execute("SELECT ngayhoc FROM diemdanh WHERE mssv = ?", (mssv,))
rows = cursor.fetchall()
ngay_list = [r[0] for r in rows]
so_buoi = len(ngay_list)

counter = defaultdict(int)
for ngay in ngay_list:
    counter[ngay] += 1
conn.close()

df_data = pd.DataFrame({
    "Ngày học": list(counter.keys()),
    "Số lần điểm danh": list(counter.values())
})

output_file = f"thongke.{mssv}.xlsx"
with pd.ExcelWriter(output_file, engine='xlsxwriter') as writer:
    df_data.to_excel(writer, sheet_name='ThongKe', index=False, startrow=4)

    workbook  = writer.book
    worksheet = writer.sheets['ThongKe']

    # Header
    worksheet.write("A1", f"Họ tên: {hoten}")
    worksheet.write("A2", f"MSSV: {mssv}")
    worksheet.write("A3", f"Số buổi đã học: {so_buoi}")

    # Thêm biểu đồ cột
    chart = workbook.add_chart({'type': 'column'})
    chart.add_series({
        'name': 'Số lần điểm danh',
        'categories': f'=ThongKe!$A$5:$A${len(df_data)+4}',
        'values':     f'=ThongKe!$B$5:$B${len(df_data)+4}',
    })
    chart.set_title({'name': 'Biểu đồ số lần điểm danh'})
    chart.set_x_axis({'name': 'Ngày học'})
    chart.set_y_axis({'name': 'Số lần'})
    worksheet.insert_chart('D2', chart)

print(f"✅ Đã xuất file Excel đầy đủ: {output_file}")
