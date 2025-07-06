# GUI/traindata.py

import customtkinter
from tkinter import messagebox
import cv2
import os
import numpy as np
import json
import threading
import sys

# Định nghĩa đường dẫn gốc của dự án
# __file__ -> .../src/GUI/traindata.py
# dirname -> .../src/GUI
# dirname -> .../src
# dirname -> .../ (Thư mục gốc)
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Lớp này dùng để chuyển hướng luồng stdout (lệnh print) vào Textbox
class TextboxRedirector:
    def __init__(self, textbox):
        self.textbox = textbox

    def write(self, text):
        self.textbox.insert("end", text)
        self.textbox.see("end") # Tự động cuộn xuống cuối

    def flush(self):
        pass

class TrainDataWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Huấn Luyện Dữ Liệu")
        self.geometry("600x400")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.on_closing)
        self.transient(parent)
        self.grab_set()

        self.is_training = False
        self.training_thread = None

        # --- Tạo các widget ---
        self.title_label = customtkinter.CTkLabel(self, text="Tiến Trình Huấn Luyện", font=customtkinter.CTkFont(size=16, weight="bold"))
        self.title_label.pack(pady=10)

        self.log_textbox = customtkinter.CTkTextbox(self, height=200, corner_radius=10)
        self.log_textbox.pack(pady=10, padx=20, fill="both", expand=True)

        self.progressbar = customtkinter.CTkProgressBar(self, corner_radius=10)
        self.progressbar.pack(pady=10, padx=20, fill="x")
        self.progressbar.set(0)

        self.start_button = customtkinter.CTkButton(self, text="Bắt Đầu Huấn Luyện", command=self.start_training_thread, height=40)
        self.start_button.pack(pady=10, padx=20, fill="x")

        self.close_button = customtkinter.CTkButton(self, text="Đóng", command=self.on_closing, fg_color="gray")
        self.close_button.pack(pady=10, padx=20)
        
    def start_training_thread(self):
        if self.is_training:
            messagebox.showwarning("Đang bận", "Quá trình huấn luyện đang diễn ra.")
            return

        self.is_training = True
        self.start_button.configure(state="disabled", text="Đang huấn luyện...")
        self.progressbar.start()
        
        self.log_textbox.delete("1.0", "end")

        self.training_thread = threading.Thread(target=self.run_training_logic)
        self.training_thread.daemon = True
        self.training_thread.start()

    def run_training_logic(self):
        original_stdout = sys.stdout
        sys.stdout = TextboxRedirector(self.log_textbox)

        try:
            # --- Tích hợp logic từ train.py ---
            dataset_path = os.path.join(ROOT_DIR, 'src', 'luu')
            model_path = os.path.join(ROOT_DIR, "model.yml")
            label_map_path = os.path.join(ROOT_DIR, "label_map.json")

            if not os.path.exists(dataset_path) or not os.listdir(dataset_path):
                print("❌ THẤT BẠI: Thư mục 'luu' chứa ảnh để huấn luyện không tồn tại hoặc trống rỗng.")
                raise ValueError("Không có dữ liệu ảnh.")

            print("Bắt đầu quá trình huấn luyện...\n")
            faces = []
            labels = []
            mssv_to_id = {}
            id_to_mssv = {}
            current_id = 0

            print("1. Đang đọc và xử lý dữ liệu ảnh...")
            all_files = os.listdir(dataset_path)
            jpg_files = [f for f in all_files if f.endswith(".jpg")]
            
            if not jpg_files:
                print("❌ THẤT BẠI: Không tìm thấy file .jpg nào trong thư mục 'luu'.")
                raise ValueError("Không có file ảnh .jpg.")

            for filename in jpg_files:
                try:
                    mssv = filename.split(".")[1]
                    if mssv not in mssv_to_id:
                        mssv_to_id[mssv] = current_id
                        id_to_mssv[current_id] = mssv
                        print(f"  - Ánh xạ mới: {mssv} -> ID {current_id}")
                        current_id += 1
                    
                    img_path = os.path.join(dataset_path, filename)
                    img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
                    if img is None:
                        print(f"  - Cảnh báo: Không thể đọc file ảnh {filename}")
                        continue
                        
                    faces.append(img)
                    labels.append(mssv_to_id[mssv])
                except IndexError:
                    print(f"  - Cảnh báo: Tên file {filename} không đúng định dạng, bỏ qua.")
                    continue
            
            print(f"\n-> Đã xử lý {len(faces)} khuôn mặt của {len(id_to_mssv)} sinh viên.")
            
            if not faces:
                print("❌ THẤT BẠI: Không có khuôn mặt nào hợp lệ để huấn luyện.")
                raise ValueError("Dữ liệu rỗng.")

            print("\n2. Đang huấn luyện mô hình nhận diện (LBPH)...")
            recognizer = cv2.face.LBPHFaceRecognizer_create()
            recognizer.train(faces, np.array(labels))
            
            print("\n3. Đang lưu các file đã huấn luyện...")
            recognizer.save(model_path)
            print(f"  - Đã lưu mô hình vào: model.yml")

            with open(label_map_path, "w") as f:
                json.dump(id_to_mssv, f)
            print(f"  - Đã lưu bản đồ ID-MSSV vào: label_map.json")
            
            print("\n🎉 HUẤN LUYỆN THÀNH CÔNG! 🎉")
            # Hiển thị messagebox phải được gọi từ luồng chính
            self.after(100, lambda: messagebox.showinfo("Hoàn thành", "Quá trình huấn luyện dữ liệu đã hoàn tất thành công!"))

        except Exception as e:
            error_message = f"\n❌ ĐÃ XẢY RA LỖI: {e}"
            print(error_message)
            self.after(100, lambda: messagebox.showerror("Lỗi", f"Quá trình huấn luyện thất bại.\nChi tiết: {e}"))
        finally:
            self.is_training = False
            self.progressbar.stop()
            self.progressbar.set(0)
            self.start_button.configure(state="normal", text="Bắt Đầu Huấn Luyện")
            sys.stdout = original_stdout

    def on_closing(self):
        if self.is_training:
            messagebox.showwarning("Đang huấn luyện", "Không thể đóng cửa sổ trong khi đang huấn luyện.")
            return
        self.destroy()