# GUI/quanlyfilelop.py

import customtkinter
from tkinter import messagebox, filedialog
import os
import shutil

# Định nghĩa đường dẫn gốc của dự án
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class QuanLyFileLopWindow(customtkinter.CTkToplevel):
    def __init__(self, parent):
        super().__init__(parent)

        self.title("Quản Lý File Danh Sách Lớp")
        self.geometry("600x500")
        self.resizable(False, False)
        self.protocol("WM_DELETE_WINDOW", self.destroy)
        self.transient(parent)
        self.grab_set()

        # --- Các biến và đường dẫn ---
        self.data_dir = os.path.join(ROOT_DIR, 'src', 'data-da21ttabc')
        os.makedirs(self.data_dir, exist_ok=True) # Tự tạo thư mục nếu chưa có

        # --- Tạo widget ---
        self.main_frame = customtkinter.CTkFrame(self, corner_radius=10)
        self.main_frame.pack(pady=20, padx=20, fill="both", expand=True)

        title_label = customtkinter.CTkLabel(self.main_frame, text="Danh Sách File Lớp Hiện Có", font=customtkinter.CTkFont(size=16, weight="bold"))
        title_label.pack(pady=10)

        # Khung cuộn để hiển thị danh sách file
        self.scrollable_frame = customtkinter.CTkScrollableFrame(self.main_frame, corner_radius=10)
        self.scrollable_frame.pack(pady=10, padx=10, fill="both", expand=True)

        # Khung chứa các nút điều khiển
        self.button_frame = customtkinter.CTkFrame(self.main_frame, fg_color="transparent")
        self.button_frame.pack(pady=10, padx=10, fill="x")
        self.button_frame.grid_columnconfigure((0, 1), weight=1)

        self.add_button = customtkinter.CTkButton(self.button_frame, text="Thêm File Mới...", command=self.add_new_file)
        self.add_button.grid(row=0, column=0, padx=5, sticky="ew")

        self.refresh_button = customtkinter.CTkButton(self.button_frame, text="Làm Mới Danh Sách", command=self.refresh_file_list)
        self.refresh_button.grid(row=0, column=1, padx=5, sticky="ew")

        # Tải danh sách file lần đầu
        self.refresh_file_list()

    def refresh_file_list(self):
        """Xóa và tải lại danh sách file trong khung cuộn."""
        # Xóa các widget cũ
        for widget in self.scrollable_frame.winfo_children():
            widget.destroy()

        try:
            excel_files = sorted([f for f in os.listdir(self.data_dir) if f.endswith(".xlsx")])
            
            if not excel_files:
                no_file_label = customtkinter.CTkLabel(self.scrollable_frame, text="Chưa có file danh sách lớp nào.", text_color="gray")
                no_file_label.pack(pady=20)
                return

            for filename in excel_files:
                # Tạo một khung nhỏ cho mỗi file
                file_item_frame = customtkinter.CTkFrame(self.scrollable_frame)
                file_item_frame.pack(pady=5, padx=5, fill="x")
                file_item_frame.grid_columnconfigure(0, weight=1)

                # Tên file
                file_label = customtkinter.CTkLabel(file_item_frame, text=filename, anchor="w")
                file_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

                # Nút xóa
                delete_button = customtkinter.CTkButton(
                    file_item_frame, 
                    text="Xóa", 
                    fg_color="red", 
                    hover_color="#C21807",
                    width=60,
                    command=lambda f=filename: self.delete_file(f) # Dùng lambda để truyền đúng tên file
                )
                delete_button.grid(row=0, column=1, padx=10, pady=5, sticky="e")

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể đọc danh sách file: {e}")

    def add_new_file(self):
        """Mở hộp thoại để chọn và thêm file Excel mới."""
        filepath = filedialog.askopenfilename(
            title="Chọn file Excel danh sách lớp",
            filetypes=[("Excel Files", "*.xlsx"), ("All Files", "*.*")]
        )
        if not filepath: # Nếu người dùng bấm Cancel
            return

        try:
            destination_path = os.path.join(self.data_dir, os.path.basename(filepath))
            if os.path.exists(destination_path):
                if messagebox.askyesno("Xác nhận", "File đã tồn tại. Bạn có muốn ghi đè không?"):
                    shutil.copy(filepath, destination_path)
                else:
                    return
            else:
                shutil.copy(filepath, destination_path)
            
            messagebox.showinfo("Thành công", f"Đã thêm file '{os.path.basename(filepath)}' thành công.")
            self.refresh_file_list() # Cập nhật lại danh sách

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể thêm file: {e}")

    def delete_file(self, filename_to_delete):
        """Xóa một file được chọn sau khi xác nhận."""
        if not messagebox.askyesno("Xác nhận xóa", f"Bạn có chắc chắn muốn xóa file '{filename_to_delete}' không?"):
            return

        try:
            file_to_delete_path = os.path.join(self.data_dir, filename_to_delete)
            os.remove(file_to_delete_path)
            messagebox.showinfo("Thành công", f"Đã xóa file '{filename_to_delete}' thành công.")
            self.refresh_file_list() # Cập nhật lại danh sách

        except Exception as e:
            messagebox.showerror("Lỗi", f"Không thể xóa file: {e}")