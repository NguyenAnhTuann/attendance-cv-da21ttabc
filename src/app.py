import os
import sys
import tkinter as tk
from tkinter import messagebox
import subprocess
import threading
from tkinter import scrolledtext, simpledialog

# Đảm bảo console dùng UTF-8 để không lỗi khi nhập tiếng Việt
if sys.platform == "win32":
    import ctypes
    ctypes.windll.kernel32.SetConsoleCP(65001)
    ctypes.windll.kernel32.SetConsoleOutputCP(65001)

def laydulieu_khuonmat():
    popup = tk.Toplevel(root)
    popup.title("Lấy dữ liệu khuôn mặt")
    popup.geometry("600x400")

    txt = scrolledtext.ScrolledText(popup, width=70, height=20, state='disabled', wrap=tk.WORD)
    txt.pack(padx=10, pady=10, fill='both', expand=True)

    def append(text):
        txt['state'] = 'normal'
        txt.insert(tk.END, text)
        txt.see(tk.END)
        txt['state'] = 'disabled'

    def run_script():
        proc = subprocess.Popen(
            ["python", "GetDatabase.py"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            stdin=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        for line in proc.stdout:
            append(line)
            if "Chọn" in line:
                choice = simpledialog.askstring("Lựa chọn", "Bạn đã nhập thông tin trước đó chưa? (1 hoặc 2)", parent=popup)
                if choice:
                    proc.stdin.write(choice + "\n")
                    proc.stdin.flush()
        proc.wait()
        append(f"\n--- Hoàn tất với mã trả về: {proc.returncode} ---\n")

    threading.Thread(target=run_script, daemon=True).start()

def train_khuonmat():
    model_path = "model.yml"
    if os.path.exists(model_path):
        os.remove(model_path)
        messagebox.showinfo("Thông báo", "🗑️ Đã xoá model cũ.")
    os.system("python train.py")

def diemdanh_sinhvien():
    os.system("python main.py")

def quanly_file_lop():
    folder = "data-da21ttabc"
    files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]
    msg = "📂 Danh sách file lớp hiện có:\n" + "\n".join(files)
    messagebox.showinfo("Danh sách lớp", msg)

    them = messagebox.askyesno("Thêm file", "📥 Bạn có muốn thêm file mới không?")
    if them:
        from tkinter import filedialog
        duongdan = filedialog.askopenfilename(title="Chọn file Excel", filetypes=[("Excel files", "*.xlsx")])
        if duongdan:
            tenfile = os.path.basename(duongdan)
            os.system(f'copy "{duongdan}" "{folder}\\{tenfile}"')
            messagebox.showinfo("✅ Thành công", f"Đã thêm {tenfile} vào thư mục lớp.")
        else:
            messagebox.showerror("❌ Lỗi", "File không tồn tại hoặc không chọn file.")

def thongke_chitiet_sinhvien():
    os.system("python thongke.py")

def thongke_theo_ngay():
    os.system("python thongke_tungngay.py")

def thongke_nhieu_ngay():
    os.system("python thongke_nhieungay.py")

# Giao diện chính
root = tk.Tk()
root.title("📘 Phần mềm quản lý điểm danh Khuôn mặt")
root.geometry("500x450")
root.resizable(False, False)

label = tk.Label(root, text="MENU QUẢN LÝ", font=("Arial", 14, "bold"))
label.pack(pady=10)

btns = [
    ("1. Lấy dữ liệu khuôn mặt", laydulieu_khuonmat),
    ("2. Train dữ liệu khuôn mặt (xoá model cũ)", train_khuonmat),
    ("3. Điểm danh sinh viên", diemdanh_sinhvien),
    ("4. Xem/Thêm file danh sách sinh viên", quanly_file_lop),
    ("5. Thống kê chi tiết sinh viên", thongke_chitiet_sinhvien),
    ("6. Thống kê điểm danh theo ngày", thongke_theo_ngay),
    ("7. Thống kê điểm danh nhiều ngày", thongke_nhieu_ngay),
    ("Thoát", root.quit)
]

for text, func in btns:
    tk.Button(root, text=text, width=40, height=2, command=func).pack(pady=5)

root.mainloop()
