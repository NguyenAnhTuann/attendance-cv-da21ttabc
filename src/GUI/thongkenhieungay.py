# GUI/thongkenhieungay.py

import customtkinter
from tkinter import messagebox, filedialog
import sqlite3
import pandas as pd
import os
import re
import unicodedata
from datetime import datetime
import threading

# Định nghĩa đường dẫn gốc của dự án
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ThongKeNhieuNgayWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Thống Kê Điểm Danh Nhiều Ngày")
        self.geometry("500x350")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()

        # --- Các biến trạng thái ---
        self.is_processing = False
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db')
        self.class_data_dir = os.path.join(ROOT_DIR, 'src', 'data-da21ttabc')

        # --- Tạo widget ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        title_label = customtkinter.CTkLabel(self.main_frame, text="Thống Kê Lớp Nhiều Ngày", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)

        # 1. Chọn Lớp
        label_lop = customtkinter.CTkLabel(self.main_frame, text="Chọn danh sách lớp:")
        label_lop.pack(anchor="w", padx=20, pady=(10,0))
        excel_files = sorted([f for f in os.listdir(self.class_data_dir) if f.endswith(".xlsx")])
        self.combo_lop = customtkinter.CTkComboBox(self.main_frame, values=excel_files, command=self.on_class_select)
        self.combo_lop.pack(fill="x", padx=20, pady=5)
        if not excel_files:
            self.combo_lop.set("Không tìm thấy file lớp nào")
            self.combo_lop.configure(state="disabled")
        else:
            self.combo_lop.set(excel_files[0])

        # 2. Chọn Môn học
        label_monhoc = customtkinter.CTkLabel(self.main_frame, text="Chọn môn học:")
        label_monhoc.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_monhoc = customtkinter.CTkComboBox(self.main_frame, values=[], state="disabled")
        self.combo_monhoc.pack(fill="x", padx=20, pady=5)

        # 3. Nút xuất Excel
        self.export_button = customtkinter.CTkButton(self.main_frame, text="Xuất Báo Cáo Tổng Hợp", command=self.start_export_thread, height=40, state="disabled")
        self.export_button.pack(fill="x", padx=20, pady=20)

        # 4. Nút đóng
        self.close_button = customtkinter.CTkButton(self, text="Đóng", command=self.on_closing, fg_color="gray")
        self.close_button.pack(pady=(0, 20))
        
        if excel_files:
            self.on_class_select(self.combo_lop.get())

    def on_class_select(self, selected_class_file):
        try:
            file_path = os.path.join(self.class_data_dir, selected_class_file)
            df = pd.read_excel(file_path)
            danh_sach_mssv = df["MSSV"].astype(str).tolist()

            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            placeholders = ','.join('?' for _ in danh_sach_mssv)
            cursor.execute(f"SELECT DISTINCT monhoc FROM diemdanh WHERE mssv IN ({placeholders})", danh_sach_mssv)
            mon_list = [row[0] for row in cursor.fetchall()]
            conn.close()

            if not mon_list:
                self.combo_monhoc.configure(values=["Lớp này chưa có dữ liệu"], state="disabled")
                self.combo_monhoc.set("Lớp này chưa có dữ liệu")
                self.export_button.configure(state="disabled")
            else:
                self.combo_monhoc.configure(values=mon_list, state="normal")
                self.combo_monhoc.set(mon_list[0])
                self.export_button.configure(state="normal")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể tải danh sách môn học: {e}")
            self.combo_monhoc.configure(values=[], state="disabled")
            self.export_button.configure(state="disabled")

    def start_export_thread(self):
        if self.is_processing:
            messagebox.showwarning("Đang xử lý", "Hệ thống đang xuất file, vui lòng đợi.")
            return

        safe_monhoc = self._to_filename(self.combo_monhoc.get())
        class_filename = os.path.splitext(self.combo_lop.get())[0]
        suggested_filename = f"thongke_tonghop_{class_filename}_{safe_monhoc}.xlsx"
        
        output_path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu file báo cáo tổng hợp",
            initialfile=suggested_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if not output_path: return
            
        self.is_processing = True
        self.export_button.configure(state="disabled", text="Đang xử lý...")
        
        export_thread = threading.Thread(target=self.run_export_logic, args=(output_path,))
        export_thread.daemon = True
        export_thread.start()

    def run_export_logic(self):
        try:
            selected_class_file = self.combo_lop.get()
            monhoc = self.combo_monhoc.get()
            
            filepath = os.path.join(self.class_data_dir, selected_class_file)
            df_lop = pd.read_excel(filepath)
            danh_sach_mssv = df_lop["MSSV"].astype(str).tolist()

            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            
            cursor.execute("SELECT DISTINCT ngayhoc FROM diemdanh WHERE monhoc = ? ORDER BY substr(ngayhoc, 7, 4), substr(ngayhoc, 4, 2), substr(ngayhoc, 1, 2)", (monhoc,))
            ngayhoc_list = [r[0] for r in cursor.fetchall()]

            if not ngayhoc_list:
                raise ValueError("Không có dữ liệu điểm danh nào cho môn học này.")

            data = []
            for index, row in df_lop.iterrows():
                mssv = str(row["MSSV"])
                hoten = row["Họ tên"]
                malop = row["Mã lớp"]
                tenlop = row.get("Tên lớp", "")
                diemdanh_status = []

                for ngay in ngayhoc_list:
                    cursor.execute("SELECT COUNT(*) FROM diemdanh WHERE mssv = ? AND ngayhoc = ? AND monhoc = ?", (mssv, ngay, monhoc))
                    has_attendance = cursor.fetchone()[0] > 0
                    diemdanh_status.append("✓" if has_attendance else "x")

                tong_hientien = diemdanh_status.count("✓")
                tong_vang = diemdanh_status.count("x")
                data.append([index + 1, mssv, hoten, malop, tenlop] + diemdanh_status + [tong_hientien, tong_vang])
            conn.close()

            columns = ["STT", "MSSV", "Họ tên", "Mã lớp", "Tên lớp"] + ngayhoc_list + ["Hiện diện", "Vắng"]
            df_output = pd.DataFrame(data, columns=columns)

            totals_row = [""] * 5
            for col in ngayhoc_list:
                col_data = df_output[col]
                totals_row.append(f"✓ {sum(col_data == '✓')}\nx {sum(col_data == 'x')}")
            totals_row += ["", ""]
            df_output.loc['Tổng kết'] = totals_row

            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df_output.to_excel(writer, sheet_name="ThongKeTongHop", index=False, startrow=3)
                workbook = writer.book
                worksheet = writer.sheets["ThongKeTongHop"]
                header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
                for col_num, value in enumerate(df_output.columns.values):
                    worksheet.write(3, col_num, value, header_format)
                worksheet.set_column(2, 2, 25) # Mở rộng cột Họ tên
                worksheet.write("A1", f"📘 Môn học: {monhoc}")
                worksheet.write("A2", f"📆 Tổng số ngày học đã điểm danh: {len(ngayhoc_list)}")
            
            self.after(100, lambda: messagebox.showinfo("Thành công", f"Đã xuất báo cáo tổng hợp thành công!\nFile được lưu tại: {output_path}"))

        except Exception as e:
            self.after(100, lambda: messagebox.showerror("Lỗi", f"Xuất file thất bại: {e}"))
        finally:
            self.is_processing = False
            self.export_button.configure(state="normal", text="Xuất Báo Cáo Tổng Hợp")

    def _to_filename(self, text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'\s+', '', text)
        return text.lower()

    def on_closing(self):
        if self.is_processing:
            messagebox.showwarning("Đang xử lý", "Không thể đóng cửa sổ trong khi đang xuất file.")
            return
        self.destroy()