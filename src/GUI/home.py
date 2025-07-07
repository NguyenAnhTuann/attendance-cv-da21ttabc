# GUI/home.py (Phiên bản Dashboard, tích hợp toàn bộ chức năng)

import sys
import os
import threading
import sqlite3
from datetime import datetime
import pickle
import json
import shutil
from tkinter import messagebox, filedialog
import re
import unicodedata
from collections import defaultdict

import customtkinter
from PIL import Image
import cv2
import numpy as np
import pandas as pd
from googleapiclient.discovery import build # type: ignore
from google_auth_oauthlib.flow import InstalledAppFlow # type: ignore
from google.auth.transport.requests import Request # type: ignore
from googleapiclient.http import MediaFileUpload # type: ignore
from unidecode import unidecode

# --- Thiết lập đường dẫn ---
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

# --- Import các cửa sổ con còn lại ---
# Chỉ còn lại cửa sổ Điểm danh là Toplevel
from src.GUI.diemdanh import DiemDanhWindow

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

# --- Lớp chuyển hướng stdout cho Textbox ---
class TextboxRedirector:
    def __init__(self, textbox):
        self.textbox = textbox
    def write(self, text):
        self.textbox.configure(state="normal")
        self.textbox.insert("end", text)
        self.textbox.see("end")
        self.textbox.configure(state="disabled")
    def flush(self):
        pass

# ===================================================================
# SECTION: KHUNG NHÌN QUẢN LÝ FILE LỚP
# ===================================================================
class QuanLyFileLopView(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.data_dir = os.path.join(ROOT_DIR, 'src', 'data-da21ttabc')
        os.makedirs(self.data_dir, exist_ok=True)
        self.main_padding_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_padding_frame.pack(pady=20, padx=20, fill="both", expand=True)
        title_label = customtkinter.CTkLabel(self.main_padding_frame, text="Danh Sách File Lớp Hiện Có", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10, padx=10)
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.main_padding_frame, corner_radius=10)
        self.scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)
        self.button_frame = customtkinter.CTkFrame(self.main_padding_frame, fg_color="transparent")
        self.button_frame.pack(pady=10, padx=10, fill="x")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)
        self.add_button = customtkinter.CTkButton(self.button_frame, text="Thêm File Mới...", command=self.add_new_file)
        self.add_button.grid(row=0, column=0, padx=5, sticky="ew")
        self.refresh_button = customtkinter.CTkButton(self.button_frame, text="Làm Mới Danh Sách", command=self.refresh_file_list)
        self.refresh_button.grid(row=0, column=1, padx=5, sticky="ew")
        self.refresh_file_list()
    def refresh_file_list(self):
        for widget in self.scrollable_frame.winfo_children(): widget.destroy()
        try:
            excel_files = sorted([f for f in os.listdir(self.data_dir) if f.endswith(".xlsx")])
            if not excel_files:
                no_file_label = customtkinter.CTkLabel(self.scrollable_frame, text="Chưa có file danh sách lớp nào.", text_color="red"); no_file_label.pack(pady=20); return
            for filename in excel_files:
                file_item_frame = customtkinter.CTkFrame(self.scrollable_frame); file_item_frame.pack(pady=5, padx=5, fill="x"); file_item_frame.grid_columnconfigure(0, weight=1)
                file_label = customtkinter.CTkLabel(file_item_frame, text=filename, anchor="w"); file_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")
                delete_button = customtkinter.CTkButton(file_item_frame, text="Xóa", fg_color="red", hover_color="#C21807", width=60, command=lambda f=filename: self.delete_file(f)); delete_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể đọc danh sách file: {e}")
    def add_new_file(self):
        filepath = filedialog.askopenfilename(title="Chọn file Excel danh sách lớp", filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")])
        if not filepath: return
        try:
            destination_path = os.path.join(self.data_dir, os.path.basename(filepath))
            if os.path.exists(destination_path) and not messagebox.askyesno("Xác nhận", "File đã tồn tại. Bạn có muốn ghi đè không?"): return
            shutil.copy(filepath, destination_path); messagebox.showinfo("Thành công", f"Đã thêm file '{os.path.basename(filepath)}' thành công."); self.refresh_file_list()
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể thêm file: {e}")
    def delete_file(self, filename_to_delete):
        if not messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa file '{filename_to_delete}' không?"): return
        try: os.remove(os.path.join(self.data_dir, filename_to_delete)); messagebox.showinfo("Thành công", f"Đã xóa file '{filename_to_delete}' thành công."); self.refresh_file_list()
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể xóa file: {e}")

# ===================================================================
# SECTION: KHUNG NHÌN THỐNG KÊ CÁ NHÂN
# ===================================================================
class ThongKeCaNhanView(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.is_processing = False
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db')
        self.student_info = {}
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        title_label = customtkinter.CTkLabel(self.main_frame, text="Thống Kê Điểm Danh Cá Nhân", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)
        label_mssv = customtkinter.CTkLabel(self.main_frame, text="Nhập Mã số sinh viên:")
        label_mssv.pack(anchor="w", padx=20, pady=(10,0))
        self.entry_mssv = customtkinter.CTkEntry(self.main_frame)
        self.entry_mssv.pack(fill="x", padx=20, pady=5)
        self.entry_mssv.bind("<Return>", self.check_student)
        self.check_button = customtkinter.CTkButton(self.main_frame, text="Kiểm tra sinh viên", command=self.check_student)
        self.check_button.pack(fill="x", padx=20, pady=10)
        self.info_label = customtkinter.CTkLabel(self.main_frame, text="Chưa tìm thấy sinh viên", text_color="red")
        self.info_label.pack(pady=5)
        label_monhoc = customtkinter.CTkLabel(self.main_frame, text="Chọn môn học để thống kê:")
        label_monhoc.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_monhoc = customtkinter.CTkComboBox(self.main_frame, values=[], state="disabled")
        self.combo_monhoc.pack(fill="x", padx=20, pady=5)
        self.export_button = customtkinter.CTkButton(self.main_frame, text="Xuất ra file Excel", command=self.start_export_thread, height=40, state="disabled")
        self.export_button.pack(fill="x", padx=20, pady=20)
    def check_student(self, event=None):
        mssv = self.entry_mssv.get().strip()
        if not mssv: messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập Mã số sinh viên."); return
        try:
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor()
            cursor.execute("SELECT hoten FROM sinhvien WHERE mssv = ?", (mssv,)); res = cursor.fetchone()
            if not res:
                self.info_label.configure(text=f"Không tìm thấy sinh viên có MSSV: {mssv}", text_color="red"); self.combo_monhoc.configure(values=[], state="disabled"); self.export_button.configure(state="disabled"); return
            hoten = res[0]; self.student_info = {"mssv": mssv, "hoten": hoten}; self.info_label.configure(text=f"Sinh viên: {hoten} - {mssv}", text_color="blue")
            cursor.execute("SELECT DISTINCT monhoc FROM diemdanh WHERE mssv = ?", (mssv,)); mon_list = [row[0] for row in cursor.fetchall()]; conn.close()
            if not mon_list:
                self.info_label.configure(text=f"SV {hoten} chưa có dữ liệu điểm danh.", text_color="red"); self.combo_monhoc.configure(values=[], state="disabled"); self.export_button.configure(state="disabled")
            else:
                self.combo_monhoc.configure(values=mon_list, state="readonly"); self.combo_monhoc.set(mon_list[0]); self.export_button.configure(state="normal")
        except Exception as e: messagebox.showerror("Lỗi DB", f"Không thể truy vấn cơ sở dữ liệu: {e}")
    def start_export_thread(self):
        if self.is_processing: messagebox.showwarning("Đang xử lý", "Hệ thống đang xuất file, vui lòng đợi."); return
        monhoc_filename = self._to_filename(self.combo_monhoc.get()); mssv = self.student_info["mssv"]; suggested_filename = f"thongke_{mssv}_{monhoc_filename}.xlsx"
        output_path = filedialog.asksaveasfilename(title="Chọn nơi lưu file thống kê", initialfile=suggested_filename, defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")])
        if not output_path: return
        self.is_processing = True; self.export_button.configure(state="disabled", text="Đang xử lý...")
        export_thread = threading.Thread(target=self.run_export_logic, args=(output_path,)); export_thread.daemon = True; export_thread.start()
    def run_export_logic(self, output_file_path):
        try:
            mssv, hoten, monhoc = self.student_info["mssv"], self.student_info["hoten"], self.combo_monhoc.get()
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor()
            cursor.execute("SELECT ngayhoc FROM diemdanh WHERE mssv = ? AND monhoc = ? ORDER BY ngayhoc", (mssv, monhoc)); rows = cursor.fetchall(); conn.close()
            if not rows: raise ValueError("Không có dữ liệu điểm danh cho môn học đã chọn.")
            ngay_data = defaultdict(int)
            for ngay, in rows:
                try: ngay_data[datetime.strptime(ngay.strip(), "%d/%m/%Y").strftime("%d/%m/%Y")] += 1
                except ValueError: print(f"Bỏ qua ngày không hợp lệ: {ngay}")
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                workbook = writer.book; ngay_sorted = sorted(ngay_data.items())
                df = pd.DataFrame({ "STT": range(1, len(ngay_sorted) + 1), "Ngày học (dd/mm/yyyy)": [ngay for ngay, _ in ngay_sorted], "Số lần điểm danh": [solan for _, solan in ngay_sorted] })
                sheet_name = "ThongKe"; df.to_excel(writer, sheet_name=sheet_name, index=False, startrow=5)
                worksheet = writer.sheets[sheet_name]
                worksheet.write("A1", f"Họ tên: {hoten}"); worksheet.write("A2", f"MSSV: {mssv}"); worksheet.write("A3", f"Môn học: {monhoc}"); worksheet.write("A4", f"Tổng số buổi đã điểm danh: {len(ngay_sorted)}")
                chart = workbook.add_chart({'type': 'column'}); chart.add_series({'name': monhoc, 'categories': f"='{sheet_name}'!$B$6:$B${len(df)+5}", 'values': f"='{sheet_name}'!$C$6:$C${len(df)+5}"})
                chart.set_title({'name': f"Biểu đồ điểm danh - {monhoc}"}); chart.set_x_axis({'name': 'Ngày học'}); chart.set_y_axis({'name': 'Số lần', 'major_gridlines': {'visible': True}, 'major_unit': 1})
                worksheet.insert_chart('E2', chart)
            self.after(100, lambda: messagebox.showinfo("Thành công", f"Đã xuất thống kê thành công!\nFile được lưu tại: {output_file_path}"))
        except Exception as e: self.after(100, lambda: messagebox.showerror("Lỗi", f"Xuất file thất bại: {e}"))
        finally: self.is_processing = False; self.export_button.configure(state="normal", text="Xuất ra file Excel")
    def _to_filename(self, text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[\s/\\:*?"<>|]+', '', text).lower()

# ===================================================================
# SECTION: KHUNG NHÌN THỐNG KÊ THEO NGÀY
# ===================================================================
class ThongKeTheoNgayView(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.is_processing = False
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db')
        self.class_data_dir = os.path.join(ROOT_DIR, 'src', 'data-da21ttabc')
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        title_label = customtkinter.CTkLabel(self.main_frame, text="Thống Kê Lớp Theo Ngày", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)
        label_lop = customtkinter.CTkLabel(self.main_frame, text="Chọn danh sách lớp:")
        label_lop.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_lop = customtkinter.CTkComboBox(self.main_frame, values=[], command=self.on_class_select)
        self.combo_lop.pack(fill="x", padx=20, pady=5)
        label_monhoc = customtkinter.CTkLabel(self.main_frame, text="Chọn môn học:")
        label_monhoc.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_monhoc = customtkinter.CTkComboBox(self.main_frame, values=[], state="disabled")
        self.combo_monhoc.pack(fill="x", padx=20, pady=5)
        label_ngay = customtkinter.CTkLabel(self.main_frame, text="Nhập ngày cần thống kê (dd/mm/yyyy):")
        label_ngay.pack(anchor="w", padx=20, pady=(10,0))
        self.entry_ngay = customtkinter.CTkEntry(self.main_frame)
        self.entry_ngay.pack(fill="x", padx=20, pady=5)
        self.entry_ngay.insert(0, datetime.now().strftime("%d/%m/%Y"))
        self.export_button = customtkinter.CTkButton(self.main_frame, text="Xuất ra file Excel", command=self.start_export_thread, height=40, state="disabled")
        self.export_button.pack(fill="x", padx=20, pady=20)
    def update_view_data(self):
        try:
            excel_files = sorted([f for f in os.listdir(self.class_data_dir) if f.endswith(".xlsx")])
            self.combo_lop.configure(values=excel_files)
            if not excel_files:
                self.combo_lop.set("Không tìm thấy file lớp nào"); self.combo_lop.configure(state="disabled"); self.combo_monhoc.configure(values=[], state="disabled"); self.export_button.configure(state="disabled")
            else:
                self.combo_lop.configure(state="readonly"); self.combo_lop.set(excel_files[0]); self.on_class_select(excel_files[0])
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể tải danh sách lớp: {e}")
    def on_class_select(self, selected_class_file):
        try:
            file_path = os.path.join(self.class_data_dir, selected_class_file); df = pd.read_excel(file_path); danh_sach_mssv = df["MSSV"].astype(str).tolist()
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor(); placeholders = ','.join('?' for _ in danh_sach_mssv)
            cursor.execute(f"SELECT DISTINCT monhoc FROM diemdanh WHERE mssv IN ({placeholders})", danh_sach_mssv); mon_list = [row[0] for row in cursor.fetchall()]; conn.close()
            if not mon_list:
                self.combo_monhoc.configure(values=["Lớp này chưa có dữ liệu"], state="disabled"); self.combo_monhoc.set("Lớp này chưa có dữ liệu"); self.export_button.configure(state="disabled")
            else:
                self.combo_monhoc.configure(values=mon_list, state="readonly"); self.combo_monhoc.set(mon_list[0]); self.export_button.configure(state="normal")
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể tải danh sách môn học: {e}"); self.combo_monhoc.configure(values=[], state="disabled"); self.export_button.configure(state="disabled")
    def start_export_thread(self):
        if self.is_processing: messagebox.showwarning("Đang xử lý", "Hệ thống đang xuất file, vui lòng đợi."); return
        ngayhoc_raw = self.entry_ngay.get().strip()
        try: ngayhoc_obj = datetime.strptime(ngayhoc_raw, "%d/%m/%Y")
        except ValueError: messagebox.showerror("Ngày không hợp lệ", "Vui lòng nhập ngày theo định dạng dd/mm/yyyy."); return
        safe_monhoc = self._to_filename(self.combo_monhoc.get()); suggested_filename = f"diemdanh_{safe_monhoc}_{ngayhoc_obj.strftime('%d-%m-%Y')}.xlsx"
        output_path = filedialog.asksaveasfilename(title="Chọn nơi lưu file thống kê", initialfile=suggested_filename, defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")])
        if not output_path: return
        self.is_processing = True; self.export_button.configure(state="disabled", text="Đang xử lý...")
        export_thread = threading.Thread(target=self.run_export_logic, args=(output_path,)); export_thread.daemon = True; export_thread.start()
    def run_export_logic(self, output_file_path):
        try:
            selected_class_file = self.combo_lop.get(); monhoc = self.combo_monhoc.get(); ngayhoc = self.entry_ngay.get().strip()
            file_path = os.path.join(self.class_data_dir, selected_class_file); df = pd.read_excel(file_path); danh_sach_mssv = df["MSSV"].astype(str).tolist()
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor(); trangthai = []; tong_hien_dien = 0
            for mssv in danh_sach_mssv:
                cursor.execute("SELECT 1 FROM diemdanh WHERE mssv = ? AND ngayhoc = ? AND monhoc = ?", (mssv, ngayhoc, monhoc))
                if cursor.fetchone(): trangthai.append("✓"); tong_hien_dien += 1
                else: trangthai.append("x")
            conn.close(); df["Trạng thái điểm danh"] = trangthai
            with pd.ExcelWriter(output_file_path, engine='xlsxwriter') as writer:
                df.to_excel(writer, index=False, sheet_name="DiemDanh"); workbook = writer.book; worksheet = writer.sheets['DiemDanh']
                format_yellow = workbook.add_format({'bg_color': '#FFF200', 'bold': True, 'border': 1}); last_row = len(df) + 1
                worksheet.write(last_row, 4, "Tổng hiện diện:", format_yellow); worksheet.write(last_row, 5, tong_hien_dien, format_yellow)
                worksheet.write(last_row + 1, 4, "Tổng vắng:", format_yellow); worksheet.write(last_row + 1, 5, len(danh_sach_mssv) - tong_hien_dien, format_yellow)
            self.after(100, lambda: messagebox.showinfo("Thành công", f"Đã xuất thống kê thành công!\nFile được lưu tại: {output_file_path}"))
        except Exception as e: self.after(100, lambda: messagebox.showerror("Lỗi", f"Xuất file thất bại: {e}"))
        finally: self.is_processing = False; self.export_button.configure(state="normal", text="Xuất ra file Excel")
    def _to_filename(self, text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[\s/\\:*?"<>|]+', '', text).lower()

# ===================================================================
# SECTION: KHUNG NHÌN THỐNG KÊ NHIỀU NGÀY
# ===================================================================
class ThongKeNhieuNgayView(customtkinter.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        self.is_processing = False
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db')
        self.class_data_dir = os.path.join(ROOT_DIR, 'src', 'data-da21ttabc')
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)
        title_label = customtkinter.CTkLabel(self.main_frame, text="Thống Kê Lớp Nhiều Ngày", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)
        label_lop = customtkinter.CTkLabel(self.main_frame, text="Chọn danh sách lớp:")
        label_lop.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_lop = customtkinter.CTkComboBox(self.main_frame, values=[], command=self.on_class_select)
        self.combo_lop.pack(fill="x", padx=20, pady=5)
        label_monhoc = customtkinter.CTkLabel(self.main_frame, text="Chọn môn học:")
        label_monhoc.pack(anchor="w", padx=20, pady=(10,0))
        self.combo_monhoc = customtkinter.CTkComboBox(self.main_frame, values=[], state="disabled")
        self.combo_monhoc.pack(fill="x", padx=20, pady=5)
        self.export_button = customtkinter.CTkButton(self.main_frame, text="Xuất Báo Cáo Tổng Hợp", command=self.start_export_thread, height=40, state="disabled")
        self.export_button.pack(fill="x", padx=20, pady=20)

    def update_view_data(self):
        try:
            excel_files = sorted([f for f in os.listdir(self.class_data_dir) if f.endswith(".xlsx")])
            self.combo_lop.configure(values=excel_files)
            if not excel_files:
                self.combo_lop.set("Không tìm thấy file lớp nào"); self.combo_lop.configure(state="disabled")
                self.combo_monhoc.configure(values=[], state="disabled"); self.export_button.configure(state="disabled")
            else:
                self.combo_lop.configure(state="readonly"); self.combo_lop.set(excel_files[0]); self.on_class_select(excel_files[0])
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể tải danh sách lớp: {e}")

    def on_class_select(self, selected_class_file):
        try:
            file_path = os.path.join(self.class_data_dir, selected_class_file); df = pd.read_excel(file_path); danh_sach_mssv = df["MSSV"].astype(str).tolist()
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor(); placeholders = ','.join('?' for _ in danh_sach_mssv)
            cursor.execute(f"SELECT DISTINCT monhoc FROM diemdanh WHERE mssv IN ({placeholders})", danh_sach_mssv); mon_list = [row[0] for row in cursor.fetchall()]; conn.close()
            if not mon_list:
                self.combo_monhoc.configure(values=["Lớp này chưa có dữ liệu"], state="disabled"); self.combo_monhoc.set("Lớp này chưa có dữ liệu"); self.export_button.configure(state="disabled")
            else:
                self.combo_monhoc.configure(values=mon_list, state="readonly"); self.combo_monhoc.set(mon_list[0]); self.export_button.configure(state="normal")
        except Exception as e: messagebox.showerror("Lỗi", f"Không thể tải danh sách môn học: {e}"); self.combo_monhoc.configure(values=[], state="disabled"); self.export_button.configure(state="disabled")

    def start_export_thread(self):
        if self.is_processing: messagebox.showwarning("Đang xử lý", "Hệ thống đang xuất file, vui lòng đợi."); return
        safe_monhoc = self._to_filename(self.combo_monhoc.get()); class_filename = os.path.splitext(self.combo_lop.get())[0]
        suggested_filename = f"thongke_tonghop_{class_filename}_{safe_monhoc}.xlsx"
        output_path = filedialog.asksaveasfilename(title="Chọn nơi lưu file báo cáo tổng hợp", initialfile=suggested_filename, defaultextension=".xlsx", filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")])
        if not output_path: return
        self.is_processing = True; self.export_button.configure(state="disabled", text="Đang xử lý...")
        export_thread = threading.Thread(target=self.run_export_logic, args=(output_path,)); export_thread.daemon = True; export_thread.start()

    def run_export_logic(self, output_path):
        try:
            selected_class_file = self.combo_lop.get(); monhoc = self.combo_monhoc.get()
            filepath = os.path.join(self.class_data_dir, selected_class_file); df_lop = pd.read_excel(filepath); danh_sach_mssv = df_lop["MSSV"].astype(str).tolist()
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor()
            cursor.execute("SELECT DISTINCT ngayhoc FROM diemdanh WHERE monhoc = ? ORDER BY substr(ngayhoc, 7, 4), substr(ngayhoc, 4, 2), substr(ngayhoc, 1, 2)", (monhoc,)); ngayhoc_list = [r[0] for r in cursor.fetchall()]
            if not ngayhoc_list: raise ValueError("Không có dữ liệu điểm danh nào cho môn học này.")
            data = []
            for index, row in df_lop.iterrows():
                mssv = str(row["MSSV"]); hoten = row["Họ tên"]; malop = row["Mã lớp"]; tenlop = row.get("Tên lớp", ""); diemdanh_status = []
                for ngay in ngayhoc_list:
                    cursor.execute("SELECT COUNT(*) FROM diemdanh WHERE mssv = ? AND ngayhoc = ? AND monhoc = ?", (mssv, ngay, monhoc)); has_attendance = cursor.fetchone()[0] > 0
                    diemdanh_status.append("✓" if has_attendance else "x")
                tong_hientien = diemdanh_status.count("✓"); tong_vang = diemdanh_status.count("x")
                data.append([index + 1, mssv, hoten, malop, tenlop] + diemdanh_status + [tong_hientien, tong_vang])
            conn.close()
            columns = ["STT", "MSSV", "Họ tên", "Mã lớp", "Tên lớp"] + ngayhoc_list + ["Hiện diện", "Vắng"]
            df_output = pd.DataFrame(data, columns=columns); totals_row = [""] * 5
            for col in ngayhoc_list: col_data = df_output[col]; totals_row.append(f"✓ {sum(col_data == '✓')}\nx {sum(col_data == 'x')}")
            totals_row += ["", ""]; df_output.loc['Tổng kết'] = totals_row
            with pd.ExcelWriter(output_path, engine='xlsxwriter') as writer:
                df_output.to_excel(writer, sheet_name="ThongKeTongHop", index=False, startrow=3); workbook = writer.book; worksheet = writer.sheets["ThongKeTongHop"]
                header_format = workbook.add_format({'bold': True, 'text_wrap': True, 'valign': 'top', 'fg_color': '#D7E4BC', 'border': 1})
                for col_num, value in enumerate(df_output.columns.values): worksheet.write(3, col_num, value, header_format)
                worksheet.set_column(2, 2, 25); worksheet.write("A1", f"📘 Môn học: {monhoc}"); worksheet.write("A2", f"📆 Tổng số ngày học đã điểm danh: {len(ngayhoc_list)}")
            self.after(100, lambda: messagebox.showinfo("Thành công", f"Đã xuất báo cáo tổng hợp thành công!\nFile được lưu tại: {output_path}"))
        except Exception as e: self.after(100, lambda: messagebox.showerror("Lỗi", f"Xuất file thất bại: {e}"))
        finally: self.is_processing = False; self.export_button.configure(state="normal", text="Xuất Báo Cáo Tổng Hợp")

    def _to_filename(self, text):
        text = unicodedata.normalize('NFKD', text).encode('ascii', 'ignore').decode('utf-8')
        return re.sub(r'[\s/\\:*?"<>|]+', '', text).lower()

# ===================================================================
# SECTION: LỚP ỨNG DỤNG CHÍNH
# ===================================================================
class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.state('zoomed'); self.title("Phần Mềm Điểm Danh Sinh Viên TVU"); self.geometry("1200x720"); self.resizable(True, True); self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.cap = None; self.detector = None; self.is_capturing = False; self.is_training = False; self.capture_thread = None; self.training_thread = None; self.student_info = {}
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db'); self.cascade_path = os.path.join(ROOT_DIR, 'src', 'haarcascade_frontalface_default.xml'); self.save_image_dir = os.path.join(ROOT_DIR, 'src', 'luu'); self.token_path = os.path.join(ROOT_DIR, 'token.pickle'); self.credentials_path = os.path.join(ROOT_DIR, 'src', 'credentials.json'); self.model_path = os.path.join(ROOT_DIR, "model.yml"); self.label_map_path = os.path.join(ROOT_DIR, "label_map.json")
        self.grid_columnconfigure(0, weight=1); self.grid_columnconfigure(1, weight=3); self.grid_rowconfigure(0, weight=1)
        self.menu_frame = customtkinter.CTkFrame(self, corner_radius=10); self.menu_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew"); self.setup_menu_buttons(self.menu_frame)
        self.main_content_frame = customtkinter.CTkFrame(self, fg_color="transparent"); self.main_content_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew"); self.main_content_frame.grid_rowconfigure(0, weight=1); self.main_content_frame.grid_columnconfigure(0, weight=1)
        
        # --- Khởi tạo tất cả các view ---
        self.get_data_view = customtkinter.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.train_data_view = customtkinter.CTkFrame(self.main_content_frame, fg_color="transparent")
        self.quanly_file_lop_view = QuanLyFileLopView(self.main_content_frame, fg_color="transparent")
        self.thongke_canhan_view = ThongKeCaNhanView(self.main_content_frame, fg_color="transparent")
        self.thongke_theongay_view = ThongKeTheoNgayView(self.main_content_frame, fg_color="transparent")
        self.thongke_nhieungay_view = ThongKeNhieuNgayView(self.main_content_frame, fg_color="transparent")

        # --- Đặt các khung chồng lên nhau ---
        self.get_data_view.grid(row=0, column=0, sticky="nsew")
        self.train_data_view.grid(row=0, column=0, sticky="nsew")
        self.quanly_file_lop_view.grid(row=0, column=0, sticky="nsew")
        self.thongke_canhan_view.grid(row=0, column=0, sticky="nsew")
        self.thongke_theongay_view.grid(row=0, column=0, sticky="nsew")
        self.thongke_nhieungay_view.grid(row=0, column=0, sticky="nsew") # <-- GRID VIEW MỚI

        self.setup_get_data_ui(self.get_data_view)
        self.setup_train_data_ui(self.train_data_view)
        self.show_view("get_data")

    def setup_menu_buttons(self, parent_frame):
        title_label = customtkinter.CTkLabel(parent_frame, text="CHỨC NĂNG", font=customtkinter.CTkFont(size=20, weight="bold")); title_label.pack(pady=15)
        buttons_config = {
            "1. Lấy Dữ Liệu Khuôn Mặt": lambda: self.show_view("get_data"),
            "2. Train Dữ Liệu Khuôn Mặt": lambda: self.show_view("train_data"),
            "3. Bắt Đầu Điểm Danh": self.open_diemdanh_window,
            "4. Quản Lý File Lớp": lambda: self.show_view("quanly_file_lop"),
            "5. Thống Kê Chi Tiết": lambda: self.show_view("thongke_canhan"),
            "6. Thống Kê Theo Ngày": lambda: self.show_view("thongke_theongay"),
            "7. Thống Kê Nhiều Ngày": lambda: self.show_view("thongke_nhieungay") # <-- SỬA Ở ĐÂY
        }
        for text, command in buttons_config.items():
            fg_color = "#4CAF50" if "Điểm Danh" in text else ("#3B8ED0", "#1F6AA5"); hover_color = "#45a049" if "Điểm Danh" in text else ("#36719F", "#144870")
            button = customtkinter.CTkButton(parent_frame, text=text, command=command, height=40, fg_color=fg_color, hover_color=hover_color); button.pack(pady=7, padx=20, fill="x")

        exit_button = customtkinter.CTkButton(
            parent_frame, 
            text="THOÁT", 
            command=self.on_closing, 
            height=40, 
            fg_color=("#D35B58", "#C75450"), 
            hover_color=("#E57373", "#D32F2F")
        )
        exit_button.pack(pady=(15, 7), padx=20, fill="x", side="bottom")

    def show_view(self, view_name):
        # --- Cập nhật logic chuyển view ---
        self.get_data_view.grid_remove()
        self.train_data_view.grid_remove()
        self.quanly_file_lop_view.grid_remove()
        self.thongke_canhan_view.grid_remove()
        self.thongke_theongay_view.grid_remove()
        self.thongke_nhieungay_view.grid_remove() # <-- ẨN VIEW MỚI
        self.release_camera()

        if view_name == "get_data": self.get_data_view.grid(); self.start_camera()
        elif view_name == "train_data": self.train_data_view.grid()
        elif view_name == "quanly_file_lop": self.quanly_file_lop_view.grid(); self.quanly_file_lop_view.refresh_file_list()
        elif view_name == "thongke_canhan": self.thongke_canhan_view.grid()
        elif view_name == "thongke_theongay": self.thongke_theongay_view.grid(); self.thongke_theongay_view.update_view_data()
        elif view_name == "thongke_nhieungay": self.thongke_nhieungay_view.grid(); self.thongke_nhieungay_view.update_view_data() # <-- HIỂN THỊ VIEW MỚI

    # ... (Toàn bộ các hàm logic khác giữ nguyên) ...
    # --- BẮT ĐẦU PHẦN GIỮ NGUYÊN ---
    def setup_get_data_ui(self, parent_frame):
        parent_frame.grid_columnconfigure(0, weight=1); parent_frame.grid_columnconfigure(1, weight=2); parent_frame.grid_rowconfigure(0, weight=1)
        control_frame = customtkinter.CTkFrame(parent_frame, corner_radius=10); control_frame.grid(row=0, column=0, padx=10, pady=10, sticky="nsew")
        control_frame_title = customtkinter.CTkLabel(control_frame, text="Thông Tin Sinh Viên", font=customtkinter.CTkFont(size=16, weight="bold")); control_frame_title.pack(pady=15, padx=20)
        fields = { "Mã số sinh viên:": "entry_id", "Họ và tên:": "entry_name", "Ngày sinh (dd/mm/yyyy):": "entry_dob", "Giới tính:": "entry_gender", "Mã lớp:": "entry_class_id" }
        for label_text, attr_name in fields.items():
            label = customtkinter.CTkLabel(control_frame, text=label_text); label.pack(padx=20, pady=(10, 0), anchor="w")
            entry = customtkinter.CTkEntry(control_frame); entry.pack(padx=20, pady=5, fill="x"); setattr(self, attr_name, entry)
        self.entry_id.bind("<FocusOut>", self.check_student_db); self.entry_id.bind("<Return>", self.check_student_db)
        self.capture_button = customtkinter.CTkButton(control_frame, text="Bắt đầu lấy dữ liệu", command=self.start_capture_thread, height=40); self.capture_button.pack(padx=20, pady=20, fill="x")
        self.status_label = customtkinter.CTkLabel(control_frame, text="Trạng thái: Sẵn sàng", text_color="red"); self.status_label.pack(padx=20, pady=10)
        camera_frame = customtkinter.CTkFrame(parent_frame, corner_radius=10); camera_frame.grid(row=0, column=1, padx=(0, 10), pady=10, sticky="nsew")
        self.camera_label = customtkinter.CTkLabel(camera_frame, text=""); self.camera_label.pack(padx=10, pady=10, fill="both", expand=True)

    def setup_train_data_ui(self, parent_frame):
        title_label = customtkinter.CTkLabel(parent_frame, text="Tiến trình huấn luyện", font=customtkinter.CTkFont(size=18, weight="bold")); title_label.pack(pady=20, padx=20)
        self.train_log_textbox = customtkinter.CTkTextbox(parent_frame, height=200, corner_radius=10, state="disabled"); self.train_log_textbox.pack(pady=10, padx=20, fill="both", expand=True)
        self.train_progressbar = customtkinter.CTkProgressBar(parent_frame, corner_radius=10); self.train_progressbar.pack(pady=10, padx=20, fill="x"); self.train_progressbar.set(0)
        self.train_start_button = customtkinter.CTkButton(parent_frame, text="Bắt đầu huấn luyện", command=self.start_training_thread, height=40); self.train_start_button.pack(pady=20, padx=20, fill="x")

    def start_camera(self):
        if self.cap is None:
            try:
                self.detector = cv2.CascadeClassifier(self.cascade_path)
                if self.detector.empty(): raise IOError(f"Không thể tải file haarcascade tại: {self.cascade_path}")
                self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
                if not self.cap.isOpened(): raise IOError("Không thể mở camera.")
                self.update_camera_feed()
            except Exception as e: messagebox.showerror("Lỗi Camera", f"Không thể kết nối với camera: {e}"); self.on_closing()

    def release_camera(self):
        if self.cap and self.cap.isOpened(): self.cap.release(); self.cap = None

    def update_camera_feed(self):
        if self.cap is None: return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1); gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY); faces = self.detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces: cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            frame_resized = cv2.resize(frame, (640, 480)); cv2image = cv2.cvtColor(frame_resized, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image); ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(640, 480)); self.camera_label.configure(image=ctk_img)
        self.after(10, self.update_camera_feed)

    def check_student_db(self, event=None):
        mssv = self.entry_id.get().strip()
        if not mssv: return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        try:
            conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor(); cursor.execute("SELECT hoten, ngaysinh, gioitinh, malop FROM sinhvien WHERE mssv = ?", (mssv,)); result = cursor.fetchone(); conn.close()
            for attr_name in ["entry_name", "entry_dob", "entry_gender", "entry_class_id"]: getattr(self, attr_name).delete(0, 'end')
            if result:
                self.entry_name.insert(0, result[0] or ""); self.entry_dob.insert(0, result[1] or ""); self.entry_gender.insert(0, result[2] or ""); self.entry_class_id.insert(0, result[3] or ""); self.status_label.configure(text=f"Đã tìm thấy SV: {result[0]}", text_color="blue")
            else: self.status_label.configure(text="Không tìm thấy SV, sẵn sàng nhập mới.", text_color="red")
        except Exception as e: messagebox.showerror("Lỗi DB", f"Không thể truy vấn cơ sở dữ liệu: {e}")

    def start_capture_thread(self):
        self.student_info = { "mssv": self.entry_id.get().strip(), "hoten": self.entry_name.get().strip(), "ngaysinh": self.entry_dob.get().strip(), "gioitinh": self.entry_gender.get().strip(), "malop": self.entry_class_id.get().strip() }
        if not self.student_info["mssv"] or not self.student_info["hoten"]: messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập ít nhất Mã số và Họ tên sinh viên."); return
        if self.is_capturing: messagebox.showwarning("Đang bận", "Hệ thống đang trong quá trình chụp."); return
        self.capture_button.configure(state="disabled", text="Đang quét khuôn mặt..."); self.is_capturing = True; self.capture_thread = threading.Thread(target=self.handle_face_capture_logic); self.capture_thread.daemon = True; self.capture_thread.start()

    def handle_face_capture_logic(self):
        try:
            self.status_label.configure(text=f"Chuẩn bị cho MSSV: {self.student_info['mssv']}", text_color="blue"); self.add_data_to_db(self.student_info)
            hoten_filename = unidecode(self.student_info["hoten"]).replace(" ", ""); parent_folder_id = '1N1OTsq8waQurLzCNG6ZikzO-7x4yScwe'
            self.delete_old_folders(self.student_info["mssv"], parent_folder_id); self.delete_local_images(self.student_info["mssv"])
            today_str = datetime.now().strftime('%d-%m-%Y'); folder_name = f"{hoten_filename}.{self.student_info['mssv']}-{today_str}"; sub_folder_id = self.create_upload_folder(folder_name, parent_folder_id)
            lap = 0
            while lap < 40 and self.is_capturing:
                ret, frame = self.cap.read()
                if not ret: continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY); faces = self.detector.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]; lap += 1; self.status_label.configure(text=f"Đã chụp: {lap}/40", text_color="green")
                    filename = f"{hoten_filename}.{self.student_info['mssv']}.{lap}.jpg"; filepath = os.path.join(self.save_image_dir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True); cv2.imwrite(filepath, gray[y:y+h, x:x+w]); self.threaded_upload(filepath, filename, sub_folder_id)
                cv2.waitKey(100)
            if lap > 0: self.after(100, lambda: messagebox.showinfo("Hoàn thành", f"Đã chụp thành công {lap} ảnh."))
            else: self.after(100, lambda: messagebox.showwarning("Không thành công", "Không chụp được ảnh nào."))
        except Exception as e: self.after(100, lambda: messagebox.showerror("Lỗi", f"Đã xảy ra lỗi trong quá trình chụp: {e}"))
        finally: self.is_capturing = False; self.capture_button.configure(state="normal", text="Bắt đầu lấy dữ liệu"); self.status_label.configure(text="Trạng thái: Sẵn sàng", text_color="red")

    def start_training_thread(self):
        if self.is_training: messagebox.showwarning("Đang bận", "Quá trình huấn luyện đang diễn ra."); return
        self.is_training = True; self.train_start_button.configure(state="disabled", text="Đang huấn luyện..."); self.train_progressbar.start(); self.train_log_textbox.configure(state="normal"); self.train_log_textbox.delete("1.0", "end"); self.train_log_textbox.configure(state="disabled")
        self.training_thread = threading.Thread(target=self.run_training_logic); self.training_thread.daemon = True; self.training_thread.start()

    def run_training_logic(self):
        original_stdout = sys.stdout; sys.stdout = TextboxRedirector(self.train_log_textbox)
        try:
            print("Bắt đầu quá trình huấn luyện...\n"); faces, labels, id_to_mssv = [], [], {}; mssv_to_id, current_id = {}, 0; print("1. Đang đọc và xử lý dữ liệu ảnh...")
            if not os.path.exists(self.save_image_dir) or not os.listdir(self.save_image_dir): raise ValueError("Thư mục 'luu' chứa ảnh để huấn luyện không tồn tại hoặc trống rỗng.")
            jpg_files = [f for f in os.listdir(self.save_image_dir) if f.endswith(".jpg")]
            if not jpg_files: raise ValueError("Không tìm thấy file .jpg nào trong thư mục 'luu'.")
            for filename in jpg_files:
                try:
                    mssv = filename.split(".")[1]
                    if mssv not in mssv_to_id: mssv_to_id[mssv] = current_id; id_to_mssv[str(current_id)] = mssv; print(f"   - Ánh xạ mới: {mssv} -> ID {current_id}"); current_id += 1
                    img_path = os.path.join(self.save_image_dir, filename); img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if img is None: print(f"   - Cảnh báo: Không thể đọc file ảnh {filename}"); continue
                    faces.append(img); labels.append(mssv_to_id[mssv])
                except IndexError: print(f"   - Cảnh báo: Tên file {filename} không đúng định dạng, bỏ qua.")
            print(f"\n-> Đã xử lý {len(faces)} khuôn mặt của {len(id_to_mssv)} sinh viên.")
            if not faces: raise ValueError("Dữ liệu rỗng, không có khuôn mặt nào hợp lệ để huấn luyện.")
            print("\n2. Đang huấn luyện mô hình nhận diện (LBPH)..."); recognizer = cv2.face.LBPHFaceRecognizer_create(); recognizer.train(faces, np.array(labels))
            print("\n3. Đang lưu các file đã huấn luyện..."); recognizer.save(self.model_path); print(f"   - Đã lưu mô hình vào: model.yml")
            with open(self.label_map_path, "w") as f: json.dump(id_to_mssv, f, indent=4); print(f"   - Đã lưu bản đồ ID-MSSV vào: label_map.json")
            print("\nHUẤN LUYỆN THÀNH CÔNG!"); self.after(100, lambda: messagebox.showinfo("Hoàn thành", "Quá trình huấn luyện dữ liệu đã hoàn tất thành công!"))
        except Exception as e: error_message = f"\n❌ ĐÃ XẢY RA LỖI: {e}"; print(error_message); self.after(100, lambda: messagebox.showerror("Lỗi", f"Quá trình huấn luyện thất bại.\nChi tiết: {e}"))
        finally: self.is_training = False; self.train_progressbar.stop(); self.train_progressbar.set(0); self.train_start_button.configure(state="normal", text="Bắt Đầu Huấn Luyện"); sys.stdout = original_stdout

    def on_closing(self):
        if self.is_capturing or self.is_training:
            if messagebox.askyesno("Xác nhận thoát", "Một tiến trình đang chạy. Bạn có chắc muốn thoát không?"): self.is_capturing = False; self.is_training = False; self.release_camera(); self.destroy()
        else: self.release_camera(); self.destroy()

    def add_data_to_db(self, info):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True); conn = sqlite3.connect(self.db_path, timeout=10); cursor = conn.cursor(); cursor.execute("SELECT * FROM sinhvien WHERE mssv = ?", (info["mssv"],)); isRecordExist = cursor.fetchone()
        if isRecordExist: cursor.execute("UPDATE sinhvien SET hoten = ?, ngaysinh = ?, gioitinh = ?, malop = ? WHERE mssv = ?", (info["hoten"], info["ngaysinh"], info["gioitinh"], info["malop"], info["mssv"]))
        else: ngaytao = datetime.now().strftime('%d/%m/%Y'); cursor.execute("INSERT INTO sinhvien (mssv, hoten, ngaysinh, gioitinh, malop, ngaytao, solantruycap) VALUES (?, ?, ?, ?, ?, ?, 0)", (info["mssv"], info["hoten"], info["ngaysinh"], info["gioitinh"], info["malop"], ngaytao))
        conn.commit(); conn.close()

    def get_drive_service(self):
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token: creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token: creds.refresh(Request())
            else: flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, ['https://www.googleapis.com/auth/drive.file']); creds = flow.run_local_server(port=0)
            with open(self.token_path, 'wb') as token: pickle.dump(creds, token)
        return build('drive', 'v3', credentials=creds)

    def create_upload_folder(self, folder_name, parent_folder_id):
        service = self.get_drive_service(); folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_folder_id]}; folder = service.files().create(body=folder_metadata, fields='id').execute(); return folder.get('id')

    def upload_to_drive(self, filepath, filename, folder_id):
        try:
            service = self.get_drive_service(); file_metadata = {'name': filename, 'parents': [folder_id]}; media = MediaFileUpload(filepath, mimetype='image/jpeg'); service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        except Exception as e: print(f"Lỗi upload {filename}: {e}")

    def threaded_upload(self, filepath, filename, folder_id):
        threading.Thread(target=self.upload_to_drive, args=(filepath, filename, folder_id)).start()

    def delete_old_folders(self, mssv, parent_folder_id):
        try:
            service = self.get_drive_service(); query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '{mssv}'"; results = service.files().list(q=query, fields="files(id, name)").execute()
            for folder in results.get('files', []): service.files().delete(fileId=folder['id']).execute()
        except Exception as e: print(f"Lỗi xóa folder Drive: {e}")

    def delete_local_images(self, mssv):
        if not os.path.exists(self.save_image_dir): return
        for filename in os.listdir(self.save_image_dir):
            if mssv in filename:
                try: os.remove(os.path.join(self.save_image_dir, filename))
                except OSError as e: print(f"Lỗi xóa file local {filename}: {e}")

    def check_other_windows(self):
        toplevel_windows = [win for win in self.winfo_children() if isinstance(win, customtkinter.CTkToplevel) and win.winfo_exists()]
        if toplevel_windows: messagebox.showwarning("Thông báo", "Một cửa sổ chức năng khác đang mở. Vui lòng đóng nó trước."); toplevel_windows[0].lift(); return True
        return False

    def open_diemdanh_window(self):
        if not self.check_other_windows(): DiemDanhWindow(self)
    
if __name__ == "__main__":
    app = App()
    app.mainloop()
    Nguyen Anh TuaN
