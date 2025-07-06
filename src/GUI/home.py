# GUI/home.py (Phiên bản hoàn chỉnh cuối cùng)

from tkinter import messagebox
import customtkinter
import sys
import os

# Thiết lập đường dẫn
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(ROOT_DIR)

# Import tất cả các cửa sổ giao diện
from src.GUI.getdata import GetDataWindow
from src.GUI.traindata import TrainDataWindow 
from src.GUI.diemdanh import DiemDanhWindow
from src.GUI.quanlyfilelop import QuanLyFileLopWindow
from src.GUI.thongkecanhan import ThongKeCaNhanWindow
from src.GUI.thongketheongay import ThongKeTheoNgayWindow
from src.GUI.thongkenhieungay import ThongKeNhieuNgayWindow # <<< THÊM DÒNG NÀY

customtkinter.set_appearance_mode("System")
customtkinter.set_default_color_theme("blue")

class App(customtkinter.CTk):
    def __init__(self):
        super().__init__()
        self.title("Phần Mềm Điểm Danh Sinh Viên TVU")
        self.geometry("400x520") # Tăng chiều cao để chứa nút mới
        self.resizable(False, False)

        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        self.title_label = customtkinter.CTkLabel(self.main_frame, text="CHỨC NĂNG", font=customtkinter.CTkFont(size=20, weight="bold"))
        self.title_label.pack(pady=15)
        
        # --- Tạo tất cả các nút chức năng ---
        buttons_config = {
            "1. Lấy Dữ Liệu Khuôn Mặt": self.open_get_data_window,
            "2. Train Dữ Liệu Khuôn Mặt": self.open_train_data_window,
            "3. Bắt Đầu Điểm Danh": self.open_diemdanh_window,
            "4. Quản Lý File Lớp": self.open_quanly_file_lop_window,
            "5. Thống Kê Chi Tiết": self.open_thongke_canhan_window,
            "6. Thống Kê Theo Ngày": self.open_thongke_theongay_window,
            "7. Thống Kê Nhiều Ngày": self.open_thongke_nhieungay_window # <<< THÊM CHỨC NĂNG NÀY
        }

        for text, command in buttons_config.items():
            fg_color = "#4CAF50" if "Điểm Danh" in text else ("#3B8ED0", "#1F6AA5")
            hover_color = "#45a049" if "Điểm Danh" in text else ("#36719F", "#144870")
            
            button = customtkinter.CTkButton(self.main_frame, text=text, command=command, height=40, fg_color=fg_color, hover_color=hover_color)
            button.pack(pady=7, padx=20, fill="x")

    def check_other_windows(self):
        if any(isinstance(win, customtkinter.CTkToplevel) for win in self.winfo_children()):
            messagebox.showwarning("Thông báo", "Một cửa sổ chức năng khác đang mở. Vui lòng đóng nó trước.")
            return True
        return False

    def open_get_data_window(self):
        if not self.check_other_windows(): GetDataWindow(self)

    def open_train_data_window(self):
        if not self.check_other_windows(): TrainDataWindow(self)

    def open_diemdanh_window(self):
        if not self.check_other_windows(): DiemDanhWindow(self)
        
    def open_quanly_file_lop_window(self):
        if not self.check_other_windows(): QuanLyFileLopWindow(self)

    def open_thongke_canhan_window(self):
        if not self.check_other_windows(): ThongKeCaNhanWindow(self)

    def open_thongke_theongay_window(self):
        if not self.check_other_windows(): ThongKeTheoNgayWindow(self)
        
    def open_thongke_nhieungay_window(self): # <<< THÊM HÀM MỚI NÀY
        if not self.check_other_windows(): ThongKeNhieuNgayWindow(self)

if __name__ == "__main__":
    app = App()
    app.mainloop()