# GUI/getdata.py (Phiên bản cuối cùng, sửa lỗi Cascade Classifier và rà soát đường dẫn)

import customtkinter
from tkinter import messagebox
import cv2
import os
import threading
from PIL import Image, ImageTk
import sqlite3
from unidecode import unidecode
from datetime import datetime
import pickle
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# ROOT_DIR là thư mục gốc của dự án, ví dụ: .../ATTENDANCE-CV-DA21TTABC/
# Dựa trên cây thư mục mới nhất, ta tính lại đường dẫn gốc cho chắc chắn
# __file__ -> .../src/GUI/getdata.py
# dirname -> .../src/GUI
# dirname -> .../src
# dirname -> .../ (Thư mục gốc)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class GetDataWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Lấy Dữ Liệu Khuôn Mặt")
        self.geometry("850x700")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()
        
        # --- Các biến trạng thái của lớp ---
        self.cap = None
        self.detector = None
        self.is_capturing = False
        self.capture_thread = None
        self.student_info = {}

        self.db_path = os.path.join(ROOT_DIR, 'db', 'attendance.db') # DB ở thư mục gốc
        self.cascade_path = os.path.join(ROOT_DIR,'src', 'haarcascade_frontalface_default.xml') # File XML ở thư mục gốc
        self.save_image_dir = os.path.join(ROOT_DIR, 'src', 'luu') # Ảnh lưu nằm trong src/luu
        self.token_path = os.path.join(ROOT_DIR, 'token.pickle')
        self.credentials_path = os.path.join(ROOT_DIR, 'src', 'credentials.json')
        
        # --- Thêm bước kiểm tra an toàn cho file Cascade ---
        self.detector = cv2.CascadeClassifier(self.cascade_path)
        if self.detector.empty():
            messagebox.showerror("Lỗi nghiêm trọng", f"Không thể tải file haarcascade tại đường dẫn:\n{self.cascade_path}\n\nVui lòng kiểm tra lại file có tồn tại không và cấu trúc thư mục.")
            self.after(100, self.on_closing) # Đóng cửa sổ sau khi báo lỗi
            return
        ### <<< KẾT THÚC SỬA ĐỔI >>> ###

        # --- Cấu hình layout (giữ nguyên) ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(0, weight=1)
        # ... (Phần code còn lại trong __init__ giữ nguyên)

        # --- Khung bên trái ---
        self.control_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.control_frame.grid(row=0, column=0, padx=20, pady=20, sticky="nsew")

        self.control_frame_title = customtkinter.CTkLabel(self.control_frame, text="Thông Tin Sinh Viên", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.control_frame_title.pack(pady=15, padx=20)
        
        fields = { "Mã số sinh viên:": "entry_id", "Họ và tên:": "entry_name", "Ngày sinh (dd/mm/yyyy):": "entry_dob", "Giới tính:": "entry_gender", "Mã lớp:": "entry_class_id" }
        for label_text, attr_name in fields.items():
            label = customtkinter.CTkLabel(self.control_frame, text=label_text)
            label.pack(padx=20, pady=(10, 0), anchor="w")
            entry = customtkinter.CTkEntry(self.control_frame)
            entry.pack(padx=20, pady=5, fill="x")
            setattr(self, attr_name, entry)

        self.entry_id.bind("<FocusOut>", self.check_student_db)
        self.entry_id.bind("<Return>", self.check_student_db)

        self.capture_button = customtkinter.CTkButton(self.control_frame, text="Bắt Đầu Chụp", command=self.start_capture_thread, height=40)
        self.capture_button.pack(padx=20, pady=20, fill="x")

        self.status_label = customtkinter.CTkLabel(self.control_frame, text="Trạng thái: Sẵn sàng", text_color="red")
        self.status_label.pack(padx=20, pady=10)
        
        self.close_button = customtkinter.CTkButton(self.control_frame, text="Đóng", command=self.on_closing, fg_color="gray")
        self.close_button.pack(padx=20, pady=10, side="bottom")

        # --- Khung bên phải ---
        self.camera_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.camera_frame.grid(row=0, column=1, padx=(0, 20), pady=20, sticky="nsew")
        
        self.camera_label = customtkinter.CTkLabel(self.camera_frame, text="")
        self.camera_label.pack(padx=10, pady=10, fill="both", expand=True)
        
        self.start_camera()

    def check_student_db(self, event=None):
        mssv = self.entry_id.get().strip()
        if not mssv: return
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True) 
        try:
            conn = sqlite3.connect(self.db_path, timeout=10)
            cursor = conn.cursor()
            cursor.execute("SELECT hoten, ngaysinh, gioitinh, malop FROM sinhvien WHERE mssv = ?", (mssv,))
            result = cursor.fetchone()
            conn.close()
            for attr_name in ["entry_name", "entry_dob", "entry_gender", "entry_class_id"]:
                getattr(self, attr_name).delete(0, 'end')
            if result:
                self.entry_name.insert(0, result[0] or "")
                self.entry_dob.insert(0, result[1] or "")
                self.entry_gender.insert(0, result[2] or "")
                self.entry_class_id.insert(0, result[3] or "")
                self.status_label.configure(text=f"Đã tìm thấy SV: {result[0]}", text_color="cyan")
            else:
                self.status_label.configure(text="Không tìm thấy SV, sẵn sàng nhập mới.", text_color="orange")
        except Exception as e:
            messagebox.showerror("Lỗi DB", f"Không thể truy vấn cơ sở dữ liệu: {e}")

    def start_camera(self):
        try:
            self.cap = cv2.VideoCapture(0, cv2.CAP_DSHOW)
            if not self.cap.isOpened(): raise IOError("Không thể mở camera.")
            self.update_camera_feed()
        except Exception as e:
            messagebox.showerror("Lỗi Camera", f"Không thể kết nối với camera: {e}")
            self.on_closing()

    def update_camera_feed(self):
        if self.cap is None: return
        ret, frame = self.cap.read()
        if ret:
            frame = cv2.flip(frame, 1)
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            faces = self.detector.detectMultiScale(gray, 1.3, 5)
            for (x, y, w, h) in faces:
                cv2.rectangle(frame, (x, y), (x + w, y + h), (255, 0, 0), 2)
            cv2image = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            img = Image.fromarray(cv2image)
            ctk_img = customtkinter.CTkImage(light_image=img, dark_image=img, size=(640, 480))
            self.camera_label.configure(image=ctk_img)
        self.after(10, self.update_camera_feed)
    
    def start_capture_thread(self):
        self.student_info = { "mssv": self.entry_id.get().strip(), "hoten": self.entry_name.get().strip(), "ngaysinh": self.entry_dob.get().strip(), "gioitinh": self.entry_gender.get().strip(), "malop": self.entry_class_id.get().strip() }
        if not self.student_info["mssv"] or not self.student_info["hoten"]:
            messagebox.showwarning("Thiếu thông tin", "Vui lòng nhập ít nhất Mã số và Họ tên sinh viên.")
            return
        if self.is_capturing:
            messagebox.showwarning("Đang bận", "Hệ thống đang trong quá trình chụp.")
            return
        self.capture_button.configure(state="disabled", text="Đang chụp...")
        self.is_capturing = True
        self.capture_thread = threading.Thread(target=self.handle_face_capture_logic)
        self.capture_thread.daemon = True
        self.capture_thread.start()

    def handle_face_capture_logic(self):
        try:
            self.status_label.configure(text=f"Chuẩn bị cho MSSV: {self.student_info['mssv']}", text_color="black")
            self.add_data_to_db(self.student_info)
            hoten_filename = unidecode(self.student_info["hoten"]).replace(" ", "")
            parent_folder_id = '1N1OTsq8waQurLzCNG6ZikzO-7x4yScwe'
            self.delete_old_folders(self.student_info["mssv"], parent_folder_id)
            self.delete_local_images(self.student_info["mssv"])
            today_str = datetime.now().strftime('%d-%m-%Y')
            folder_name = f"{hoten_filename}.{self.student_info['mssv']}-{today_str}"
            sub_folder_id = self.create_upload_folder(folder_name, parent_folder_id)
            lap = 0
            while lap < 40 and self.is_capturing:
                ret, frame = self.cap.read()
                if not ret: continue
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
                faces = self.detector.detectMultiScale(gray, 1.3, 5)
                if len(faces) > 0:
                    (x, y, w, h) = faces[0]
                    lap += 1
                    self.status_label.configure(text=f"Đã chụp: {lap}/40", text_color="black")
                    filename = f"{hoten_filename}.{self.student_info['mssv']}.{lap}.jpg"
                    # Sử dụng đường dẫn đã định nghĩa ở __init__
                    filepath = os.path.join(self.save_image_dir, filename)
                    os.makedirs(os.path.dirname(filepath), exist_ok=True)
                    cv2.imwrite(filepath, gray[y:y+h, x:x+w])
                    self.threaded_upload(filepath, filename, sub_folder_id)
                cv2.waitKey(100)
            if lap > 0: messagebox.showinfo("Hoàn thành", f"Đã chụp thành công {lap} ảnh.")
            else: messagebox.showwarning("Không thành công", "Không chụp được ảnh nào.")
        except Exception as e:
            messagebox.showerror("Lỗi", f"Đã xảy ra lỗi trong quá trình chụp: {e}")
        finally:
            self.is_capturing = False
            self.capture_button.configure(state="normal", text="Bắt Đầu Chụp")
            self.status_label.configure(text="Trạng thái: Sẵn sàng", text_color="yellow")
    
    def on_closing(self):
        if self.is_capturing: self.is_capturing = False
        if self.cap and self.cap.isOpened(): self.cap.release()
        self.destroy()

    def add_data_to_db(self, info):
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path, timeout=10)
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sinhvien WHERE mssv = ?", (info["mssv"],))
        isRecordExist = cursor.fetchone()
        if isRecordExist:
            cursor.execute("UPDATE sinhvien SET hoten = ?, ngaysinh = ?, gioitinh = ?, malop = ? WHERE mssv = ?", (info["hoten"], info["ngaysinh"], info["gioitinh"], info["malop"], info["mssv"]))
        else:
            ngaytao = datetime.now().strftime('%d/%m/%Y')
            cursor.execute("INSERT INTO sinhvien (mssv, hoten, ngaysinh, gioitinh, malop, ngaytao, solantruycap) VALUES (?, ?, ?, ?, ?, ?, 0)", (info["mssv"], info["hoten"], info["ngaysinh"], info["gioitinh"], info["malop"], ngaytao))
        conn.commit()
        conn.close()

    def get_drive_service(self):
        creds = None
        if os.path.exists(self.token_path):
            with open(self.token_path, 'rb') as token: creds = pickle.load(token)
        if not creds or not creds.valid:
            if creds and creds.expired and creds.refresh_token:
                creds.refresh(Request())
            else:
                flow = InstalledAppFlow.from_client_secrets_file(self.credentials_path, ['https://www.googleapis.com/auth/drive.file'])
                creds = flow.run_local_server(port=0)
            with open(self.token_path, 'wb') as token: pickle.dump(creds, token)
        return build('drive', 'v3', credentials=creds)

    def create_upload_folder(self, folder_name, parent_folder_id):
        service = self.get_drive_service()
        folder_metadata = {'name': folder_name, 'mimeType': 'application/vnd.google-apps.folder', 'parents': [parent_folder_id]}
        folder = service.files().create(body=folder_metadata, fields='id').execute()
        return folder.get('id')

    def upload_to_drive(self, filepath, filename, folder_id):
        try:
            service = self.get_drive_service()
            file_metadata = {'name': filename, 'parents': [folder_id]}
            media = MediaFileUpload(filepath, mimetype='image/jpeg')
            service.files().create(body=file_metadata, media_body=media, fields='id').execute()
        except Exception as e: print(f"Lỗi upload {filename}: {e}")

    def threaded_upload(self, filepath, filename, folder_id):
        threading.Thread(target=self.upload_to_drive, args=(filepath, filename, folder_id)).start()

    def delete_old_folders(self, mssv, parent_folder_id):
        try:
            service = self.get_drive_service()
            query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '{mssv}'"
            results = service.files().list(q=query, fields="files(id, name)").execute()
            for folder in results.get('files', []):
                service.files().delete(fileId=folder['id']).execute()
        except Exception as e: print(f"Lỗi xóa folder Drive: {e}")

    def delete_local_images(self, mssv):
        if not os.path.exists(self.save_image_dir): return
        for filename in os.listdir(self.save_image_dir):
            if mssv in filename:
                os.remove(os.path.join(self.save_image_dir, filename))