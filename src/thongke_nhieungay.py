import os
import sqlite3
import pandas as pd
import unicodedata
import re

def to_filename(text):
    text = unicodedata.normalize('NFKD', text)
    text = text.encode('ascii', 'ignore').decode('utf-8')
    text = re.sub(r'\s+', '', text)
    return text.lower()

def main():
    # --- CHỌN FILE LỚP ---
    folder_path = "data-da21ttabc"
    excel_files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]
    print("📂 Chọn file lớp:")
    for i, file in enumerate(excel_files, 1):
        print(f"{i}. {file}")
    filename = excel_files[int(input("Nhập số: ")) - 1]
    filepath = os.path.join(folder_path, filename)
    df_lop = pd.read_excel(filepath)

    danh_sach_mssv = df_lop["MSSV"].astype(str).tolist()

    # --- LẤY DANH SÁCH MÔN HỌC có điểm danh ---
    conn = sqlite3.connect('../db/attendance.db')
    cursor = conn.cursor()
    placeholders = ','.join('?' for _ in danh_sach_mssv)
    cursor.execute(f"""
        SELECT DISTINCT monhoc
        FROM diemdanh
        WHERE mssv IN ({placeholders})
    """, danh_sach_mssv)
    mon_list = [row[0] for row in cursor.fetchall()]

    if not mon_list:
        print("❌ Không tìm thấy môn học nào có điểm danh cho lớp này.")
        return

    print("📚 Chọn môn học:")
    for i, mon in enumerate(mon_list, 1):
        print(f"{i}. {mon}")
    monhoc = mon_list[int(input("Nhập số: ")) - 1]

    # --- LẤY DANH SÁCH NGÀY ĐIỂM DANH ---
    cursor.execute("SELECT DISTINCT ngayhoc FROM diemdanh WHERE monhoc = ? ORDER BY ngayhoc", (monhoc,))
    ngayhoc_list = [r[0] for r in cursor.fetchall()]

    # --- XÂY BẢNG THỐNG KÊ ---
    data = []
    for index, row in df_lop.iterrows():
        mssv = str(row["MSSV"])
        hoten = row["Họ tên"]
        malop = row["Mã lớp"]
        tenlop = row["Tên lớp"] if "Tên lớp" in df_lop.columns else ""
        diemdanh_status = []

        for ngay in ngayhoc_list:
            cursor.execute("""
                SELECT COUNT(*) FROM diemdanh
                WHERE mssv = ? AND ngayhoc = ? AND monhoc = ?
            """, (mssv, ngay, monhoc))
            has_attendance = cursor.fetchone()[0] > 0
            diemdanh_status.append("✓" if has_attendance else "x")

        tong_hientien = diemdanh_status.count("✓")
        tong_vang = diemdanh_status.count("x")
        data.append([index + 1, mssv, hoten, malop, tenlop] + diemdanh_status + [tong_hientien, tong_vang])

    conn.close()

    # --- TẠO FILE EXCEL ---
    columns = ["STT", "MSSV", "Họ tên", "Mã lớp", "Tên lớp"] + ngayhoc_list + ["Hiện diện", "Vắng"]
    df_output = pd.DataFrame(data, columns=columns)

    # --- THÊM HÀNG TỔNG KẾT MỖI NGÀY ---
    totals = [""] * 5
    for col in ngayhoc_list:
        col_data = df_output[col]
        totals.append(f"Tổng hiện diện: {sum(col_data == '✓')}\nTổng vắng: {sum(col_data == 'x')}")
    totals += ["", ""]
    df_output.loc[len(df_output.index)] = totals

    # --- GHI FILE ---
    os.makedirs("thongke_nhieungay", exist_ok=True)
    safe_monhoc = to_filename(monhoc)
    output_filename = f"thongke_nhieungay/thongke_nhieungay_{safe_monhoc}_{filename}"

    with pd.ExcelWriter(output_filename, engine='xlsxwriter') as writer:
        df_output.to_excel(writer, sheet_name="Thống kê", index=False, startrow=3)

        workbook = writer.book
        worksheet = writer.sheets["Thống kê"]

        worksheet.write("A1", f"📘 Môn học: {monhoc}")
        worksheet.write("A2", f"📆 Tổng số ngày học: {len(ngayhoc_list)}")

    print(f"✅ Đã xuất file: {output_filename}")

if __name__ == "__main__":
    main()
