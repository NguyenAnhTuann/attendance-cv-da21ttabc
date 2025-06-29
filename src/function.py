import os

def laydulieu_khuonmat():
    os.system("python GetDatabase.py")

def train_khuonmat():
    model_path = "model.yml"
    if os.path.exists(model_path):
        os.remove(model_path)
        print("🗑️ Đã xoá model cũ.")
    os.system("python train.py")

def diemdanh_sinhvien():
    os.system("python main.py")


def quanly_file_lop():
    folder = "data-da21ttabc"
    files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]
    print("📂 Danh sách file lớp hiện có:")
    for i, f in enumerate(files, 1):
        print(f"{i}. {f}")
    them = input("📥 Bạn có muốn thêm file mới không? (y/n): ")
    if them.lower() == 'y':
        duongdan = input("🔍 Nhập đường dẫn file Excel cần thêm: ").strip()
        if os.path.exists(duongdan):
            tenfile = os.path.basename(duongdan)
            os.system(f'copy "{duongdan}" "{folder}\\{tenfile}"')
            print(f"✅ Đã thêm {tenfile} vào thư mục lớp.")
        else:
            print("❌ File không tồn tại.")

def thongke_chitiet_sinhvien():
    os.system("python thongke.py")

def thongke_theo_ngay():
    os.system("python thongke_tungngay.py")

def thongke_nhieu_ngay():
    os.system("python thongke_nhieungay.py")
    

# ===== MENU =====
while True:
    print("\n🧠 MENU QUẢN LÝ ĐIỂM DANH KHUÔN MẶT")
    print("1. Lấy dữ liệu khuôn mặt")
    print("2. Train dữ liệu khuôn mặt (xoá model cũ)")
    print("3. Điểm danh sinh viên")
    print("4. Xem/Thêm file danh sách sinh viên")
    print("5. Thống kê chi tiết sinh viên")
    print("6. Thống kê điểm danh theo ngày")
    print("7. Thống kê điểm danh nhiều ngày")
    print("0. Thoát")

    chon = input("👉 Nhập lựa chọn: ").strip()

    if chon == '1':
        laydulieu_khuonmat()
    elif chon == '2':
        train_khuonmat()
    elif chon == '3':
        diemdanh_sinhvien()
    elif chon == '4':
        quanly_file_lop()
    elif chon == '5':
        thongke_chitiet_sinhvien()
    elif chon == '6':
        thongke_theo_ngay()
    elif chon == '7':
        thongke_nhieu_ngay()
    elif chon == '0':
        print("👋 Thoát chương trình.")
        break
    else:
        print("⚠️ Lựa chọn không hợp lệ. Vui lòng thử lại.")
