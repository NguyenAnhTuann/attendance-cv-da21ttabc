# GUI/diemdanh.py (Phiên bản cuối cùng, sửa lỗi Cascade Classifier)

import customtkinter
from tkinter import messagebox
import cv2
import os
import threading
import time
from PIL import Image, ImageTk
import sqlite3
import json
import pandas as pd
from datetime import datetime
import sys

# Định nghĩa đường dẫn gốc của dự án
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TextboxRedirector:
    def __init__(self, textbox):
        self.textbox = textbox
        self.textbox.configure(state="normal")
    def write(self, text):
        self.textbox.insert("end", text)
        self.textbox.see("end")
    def flush(self):
        pass

class DiemDanhWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Điểm Danh Sinh Viên")
        self.geometry("1100x720")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()

        # --- Các biến trạng thái ---
        self.is_running = False
        self.cap = None
        self.attendance_thread = None
        self.recognizer = cv2.face.LBPHFaceRecognizer_create()
        self.id_to_mssv = {}
        self.current_frame = None
        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db')

        ### <<< THÊM MỚI / CHỈNH SỬA >>> ###
        # Thêm bước kiểm tra an toàn khi load file haarcascade
        cascade_path = os.path.join(ROOT_DIR, 'src', 'haarcascade_frontalface_default.xml')
        self.face_cascade = cv2.CascadeClassifier(cascade_path)
        if self.face_cascade.empty():
            messagebox.showerror("Lỗi nghiêm trọng", f"Không thể tải file haarcascade tại đường dẫn:\n{cascade_path}\n\nVui lòng kiểm tra lại file có tồn tại không và cấu trúc thư mục.")
            self.after(100, self.on_closing) # Đóng cửa sổ sau khi báo lỗi
            return
        ### <<< KẾT THÚC SỬA ĐỔI >>> ###

        # --- Cấu hình layout chính ---
        # ... (Toàn bộ phần code còn lại của file giữ nguyên như cũ)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)

        # --- Khung bên trái (Cấu hình và Log) ---
        self.control_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        # -- Widget Cấu hình --
        self.config_frame = customtkinter.CTkFrame(self.control_frame, fg_color="transparent")
        self.config_frame.pack(pady=10, padx=10, fill="x")
        
        config_title = customtkinter.CTkLabel(self.config_frame, text="Cấu Hình Buổi Điểm Danh", font=customtkinter.CTkFont(size=16, weight="bold"))
        config_title.pack(pady=10)

        # Chọn môn học
        mon_list = ["Thị Giác Máy Tính", "Hệ Thống Thông Tin Quản Lý", "Máy Học Ứng Dụng"]
        label_mon = customtkinter.CTkLabel(self.config_frame, text="Chọn môn học:")
        label_mon.pack(anchor="w", padx=10)
        self.combo_monhoc = customtkinter.CTkComboBox(self.config_frame, values=mon_list)
        self.combo_monhoc.pack(fill="x", padx=10, pady=5)
        self.combo_monhoc.set(mon_list[0])

        # Chọn lớp
        excel_files = [f for f in os.listdir(os.path.join(ROOT_DIR, 'src', 'data-da21ttabc')) if f.endswith(".xlsx")]
        label_lop = customtkinter.CTkLabel(self.config_frame, text="Chọn lớp:")
        label_lop.pack(anchor="w", padx=10)
        self.combo_lop = customtkinter.CTkComboBox(self.config_frame, values=excel_files)
        self.combo_lop.pack(fill="x", padx=10, pady=5)
        if excel_files: self.combo_lop.set(excel_files[0])

        # Chọn buổi học
        buoi_list = ["Sáng", "Chiều"]
        label_buoi = customtkinter.CTkLabel(self.config_frame, text="Chọn buổi học:")
        label_buoi.pack(anchor="w", padx=10)
        self.combo_buoi = customtkinter.CTkComboBox(self.config_frame, values=buoi_list)
        self.combo_buoi.pack(fill="x", padx=10, pady=5)
        self.combo_buoi.set(buoi_list[0])
        
        # Nút Bắt đầu/Dừng
        self.start_stop_button = customtkinter.CTkButton(self.config_frame, text="Bắt Đầu Điểm Danh", command=self.toggle_attendance, height=40)
        self.start_stop_button.pack(pady=20, padx=10, fill="x")

        # -- Widget Log --
        log_title = customtkinter.CTkLabel(self.control_frame, text="Nhật Ký Điểm Danh", font=customtkinter.CTkFont(size=16, weight="bold"))
        log_title.pack(pady=10)
        self.log_textbox = customtkinter.CTkTextbox(self.control_frame, corner_radius=10, state="disabled")
        self.log_textbox.pack(pady=10, padx=10, fill="both", expand=True)

        # --- Khung bên phải (Hiển thị Camera) ---
        self.camera_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.camera_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        self.camera_label = customtkinter.CTkLabel(self.camera_frame, text="Camera sẽ hiển thị ở đây\nVui lòng cấu hình và nhấn 'Bắt đầu'")
        self.camera_label.pack(padx=10, pady=10, fill="both", expand=True)

    def toggle_attendance(self):
        if self.is_running:
            self.stop_attendance()
        else:
            self.start_attendance()

    def start_attendance(self):
        try:
            model_path = os.path.join(ROOT_DIR, "model.yml")
            label_map_path = os.path.join(ROOT_DIR, "label_map.json")
            if not os.path.exists(model_path) or not os.path.exists(label_map_path):
                raise FileNotFoundError("Không tìm thấy file model.yml hoặc label_map.json. Vui lòng huấn luyện dữ liệu trước.")
            
            self.recognizer.read(model_path)
            with open(label_map_path, 'r') as f: self.id_to_mssv = json.load(f)
            
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened(): raise IOError("Không thể mở camera.")
        except Exception as e:
            messagebox.showerror("Lỗi Khởi Tạo", f"Không thể bắt đầu điểm danh: {e}")
            return
            
        self.is_running = True
        self.log_textbox.configure(state="normal")
        self.log_textbox.delete("1.0", "end")
        self.start_stop_button.configure(text="Dừng Điểm Danh", fg_color="red", hover_color="#C21807")
        self.combo_monhoc.configure(state="disabled")
        self.combo_lop.configure(state="disabled")
        self.combo_buoi.configure(state="disabled")

        self.attendance_thread = threading.Thread(target=self.run_recognition_logic)
        self.attendance_thread.daemon = True
        self.attendance_thread.start()
        self.update_camera_feed()

    def stop_attendance(self):
        self.is_running = False
        if self.attendance_thread: self.attendance_thread.join(timeout=1.0)
        
        self.start_stop_button.configure(text="Bắt Đầu Điểm Danh", fg_color=("#3B8ED0", "#1F6AA5"), hover_color=("#36719F", "#144870"))
        self.combo_monhoc.configure(state="normal")
        self.combo_lop.configure(state="normal")
        self.combo_buoi.configure(state="normal")
        
        self.camera_label.configure(image=None, text="Camera đã tắt.\nSẵn sàng cho phiên mới.")
        self.log_textbox.configure(state="disabled")

    def update_camera_feed(self):
        if not self.is_running or self.cap is None: return
        ret, frame = self.cap.read()
        if ret:
            self.current_frame = frame.copy()
            frame = cv2.flip(frame, 1)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(720, 540))
            self.camera_label.configure(image=ctk_img)
        self.after(30, self.update_camera_feed)

    def run_recognition_logic(self):
        original_stdout = sys.stdout
        sys.stdout = TextboxRedirector(self.log_textbox)
        
        monhoc = self.combo_monhoc.get()
        buoihoc = self.combo_buoi.get()
        start_str, end_str = ("07:00", "10:30") if buoihoc == "Sáng" else ("13:00", "16:30")
        start_time = datetime.strptime(start_str, "%H:%M")
        end_time = datetime.strptime(end_str, "%H:%M")
        
        recognized_ids = set()
        font = cv2.FONT_HERSHEY_SIMPLEX

        print(f"--- Bắt đầu điểm danh ---\n- Môn: {monhoc}\n- Buổi: {buoihoc}\n------------------\n")

        while self.is_running:
            if self.current_frame is None:
                time.sleep(0.1)
                continue
            
            frame_to_process = self.current_frame.copy()
            gray = cv2.cvtColor(frame_to_process, cv2.COLOR_BGR2GRAY)
            faces = self.face_cascade.detectMultiScale(gray, 1.3, 5)

            for (x, y, w, h) in faces:
                id_, confidence = self.recognizer.predict(gray[y:y + h, x:x + w])
                
                if confidence < 50:
                    mssv = self.id_to_mssv.get(str(id_))
                    if mssv and mssv not in recognized_ids:
                        recognized_ids.add(mssv)
                        now = datetime.now()
                        today = now.strftime('%d/%m/%Y')
                        current_time_str = now.strftime('%H:%M:%S')
                        gio_vao = datetime.strptime(current_time_str[:5], "%H:%M")
                        
                        if gio_vao > end_time:
                            print(f"⚠ {current_time_str} - MSSV: {mssv} đến sau giờ điểm danh.\n")
                            continue
                        
                        delay = int((gio_vao - start_time).total_seconds() // 60)
                        trangthai = "Đúng giờ" if delay <= 15 else f"Trễ {delay} phút"
                        
                        try:
                            conn = sqlite3.connect(self.db_path, timeout=10)
                            cursor = conn.cursor()
                            cursor.execute("SELECT * FROM diemdanh WHERE mssv=? AND ngayhoc=? AND monhoc=? AND buoihoc=?", (mssv, today, monhoc, buoihoc))
                            if not cursor.fetchone():
                                cursor.execute("INSERT INTO diemdanh (mssv, thoigian, ngayhoc, monhoc, trangthaivaolop, buoihoc) VALUES (?, ?, ?, ?, ?, ?)", (mssv, current_time_str, today, monhoc, trangthai, buoihoc))
                                print(f"✅ {current_time_str} - Ghi nhận: {mssv} - {trangthai}\n")
                            else:
                                print(f"ℹ️ {current_time_str} - MSSV: {mssv} đã được điểm danh buổi này.\n")
                            conn.commit()
                            conn.close()
                        except Exception as e:
                            print(f"❌ Lỗi DB: {e}\n")
            time.sleep(0.5) 

        sys.stdout = original_stdout
        if self.cap: self.cap.release()
        self.cap = None
        print("--- Luồng điểm danh đã dừng. ---")

    def on_closing(self):
        # Dừng luồng một cách an toàn trước khi đóng cửa sổ
        self.is_running = False
        # Đợi một chút để luồng có thời gian kết thúc
        # self.after(100, self.destroy) # Có thể gây lỗi nếu luồng chưa giải phóng camera
        if self.cap: self.cap.release()
        self.destroy()