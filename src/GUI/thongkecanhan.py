# GUI/thongkecanhan.py (Phiên bản cuối cùng, giống hệt chức năng file gốc)

import customtkinter
from tkinter import messagebox, filedialog
import sqlite3
import pandas as pd
import os
import re
import unicodedata
from datetime import datetime
from collections import defaultdict
import threading

# Định nghĩa đường dẫn gốc của dự án
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class ThongKeCaNhanWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Thống Kê Điểm Danh Cá Nhân")
        self.geometry("500x450")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()

        # --- Các biến trạng thái ---
        self.is_processing = False
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db')
        self.student_info = {}

        # --- Tạo widget ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        title_label = customtkinter.CTkLabel(self.main_frame, text="Thống Kê Cá Nhân", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)

        # Nhập MSSV
        label_mssv = customtkinter.CTkLabel(self.main_frame, text="Nhập Mã số sinh viên:")
        label_mssv.pack(anchor="w", padx=20, pady=(10,0))
        self.entry_mssv = customtkinter.CTkEntry(self.main_frame)
        self.entry_mssv.pack(fill="x", padx=20, pady=5)
        self.entry_mssv.bind("<Return>", self.check_student)

        self.check_button = customtkinter.CTkButton(self.main_frame, text="Kiểm tra sinh viên", command=self.check_student)
        self.check_button.pack(fill="x", padx=20, pady=10)

        # Hiển thị thông tin tìm thấy
        self.info_label = customtkinter.CTkLabel(self.main_frame, text="Chưa tìm thấy sinh viên", text_color="black")
        self.info_label.pack(pady=5)

        # Chọn môn học
        label_monhoc = customtkinter.CTkLabel(self.main_frame, text="Chọn môn học để thống kê:")
        label_monhoc.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_monhoc = customtkinter.CTkComboBox(self.main_frame, values=[], state="disabled")
        self.combo_monhoc.pack(fill="x", padx=20, pady=5)

        # Nút xuất Excel
        self.export_button = customtkinter.CTkButton(self.main_frame, text="Xuất ra file Excel", command=self.start_export_thread, height=40, state="disabled")
        self.export_button.pack(fill="x", padx=20, pady=20)

        # Nút đóng
        self.close_button = customtkinter.CTkButton(self, text="Đóng", command=self.on_closing, fg_color="gray")
        self.close_button.pack(pady=(0, 20))

    def check_student(self, event=None):
        mssv = self.entry_mssv.get().strip()
        if not mssv:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mã số sinh viên.")
            return

        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT hoten FROM sinhvien WHERE mssv = ?", (mssv,))
            res = cursor.fetchone()
            if not res:
                self.info_label.configure(text=f"Không tìm thấy sinh viên có MSSV: {mssv}", text_color="red")
                self.combo_monhoc.configure(values=[], state="disabled")
                self.export_button.configure(state="disabled")
                return
            
            hoten = res[0]
            self.student_info = {"mssv": mssv, "hoten": hoten}
            self.info_label.configure(text=f"Sinh viên: {hoten} - {mssv}", text_color="black")

            cursor.execute("SELECT DISTINCT monhoc FROM diemdanh WHERE mssv = ?", (mssv,))
            mon_list = [row[0] for row in cursor.fetchall()]
            conn.close()

            if not mon_list:
                self.info_label.configure(text=f"SV {hoten} chưa có dữ liệu điểm danh.", text_color="orange")
                self.combo_monhoc.configure(values=[], state="disabled")
                self.export_button.configure(state="disabled")
            else:
                self.combo_monhoc.configure(values=mon_list, state="normal")
                self.combo_monhoc.set(mon_list[0])
                self.export_button.configure(state="normal")

        except Exception as e:
            messagebox.showerror("Lỗi DB", f"Không thể truy vấn cơ sở dữ liệu: {e}")

    def start_export_thread(self):
        if self.is_processing:
            messagebox.showwarning("Đang xử lý", "Hệ thống đang xuất file, vui lòng đợi.")
            return
        
        # --- HỎI NGƯỜI DÙNG NƠI LƯU FILE ---
        monhoc_filename = self._to_filename(self.combo_monhoc.get())
        mssv = self.student_info["mssv"]
        suggested_filename = f"thongke_{mssv}_{monhoc_filename}.xlsx"
        
        output_path = filedialog.asksaveasfilename(
            title="Chọn nơi lưu file thống kê",
            initialfile=suggested_filename,
            defaultextension=".xlsx",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )

        if not output_path: # Nếu người dùng bấm Cancel
            return
            
        self.is_processing = True
        self.export_button.configure(state="disabled", text="Đang xử lý...")
        
        export_thread = threading.Thread(target=self.run_export_logic, args=(output_path,))
        export_thread.daemon = True
        export_thread.start()

    def run_export_logic(self, output_file_path):
        """Hàm này chứa logic y hệt file thongke.py gốc."""
        try:
            mssv = self.student_info["mssv"]
            hoten = self.student_info["hoten"]
            monhoc = self.combo_monhoc.get()
            
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT ngayhoc FROM diemdanh WHERE mssv = ? AND monhoc = ? ORDER BY ngayhoc", (mssv, monhoc))
            rows = cursor.fetchall()
            conn.close()

            if not rows:
                raise ValueError("Không có dữ liệu điểm danh cho môn học đã chọn.")

            ngay_data = defaultdict(int)
            for ngay, in rows:
                try:
                    ngay_chuan_hoa = datetime.strptime(ngay.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")
                    ngay_data[ngay_chuan_hoa] += 1
                except ValueError:
                    print(f"Bỏ qua ngày không hợp lệ: {ngay}")

            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                workbook = writer.book
                ngay_sorted = sorted(ngay_data.items())
                df = pd.DataFrame({ "STT": range(1, len(ngay_sorted) + 1), "Ngày học (dd/mm/yyyy)": [ngay for ngay, _ in ngay_sorted], "Số lần điểm danh": [solan for _, solan in ngay_sorted] })
                sheet_name = "ThongKe"
                df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=5)
                worksheet = writer.sheets[sheet_name]
                worksheet.write("A1", f"Họ tên: {hoten}")
                worksheet.write("A2", f"MSSV: {mssv}")
                worksheet.write("A3", f"Môn học: {monhoc}")
                worksheet.write("A4", f"Tổng số buổi đã điểm danh: {len(ngay_sorted)}")
                chart = workbook.add_chart({'type': 'column'})
                chart.add_series({'name': monhoc, 'categories': f"='{sheet_name}'!$B$6:$B${len(df)+5}", 'values': f"='{sheet_name}'!$C$6:$C${len(df)+5}"})
                chart.set_title({'name': f"Biểu đồ điểm danh - {monhoc}"})
                chart.set_x_axis({'name': 'Ngày học'})
                chart.set_y_axis({'name': 'Số lần', 'major_gridlines': {'visible': True}, 'major_unit': 1})
                worksheet.insert_chart('E2', chart)
            
            self.after(100, lambda: messagebox.showinfo("Thành công", f"Đã xuất thống kê thành công!\nFile được lưu tại: {output_file_path}"))

        except Exception as e:
            self.after(100, lambda: messagebox.showerror("Lỗi", f"Xuất file thất bại: {e}"))
        finally:
            self.is_processing = False
            self.export_button.configure(state="normal", text="Xuất ra file Excel")

    def _to_filename(self, text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        text = re.sub(r'\s+', '', text)
        return text.lower()

    def on_closing(self):
        if self.is_processing:
            messagebox.showwarning("Đang xử lý", "Không thể đóng cửa sổ trong khi đang xuất file.")
            return
        self.destroy()