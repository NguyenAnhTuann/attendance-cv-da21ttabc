# function.py ( phiên bản hoàn chỉnh để sử dụng với GUI )
import os
import shutil # Sử dụng shutil để copy file an toàn hơn

def laydulieu_khuonmat():
    """
    Chạy script để lấy hình ảnh khuôn mặt từ camera.
    """
    print("Bắt đầu quá trình lấy dữ liệu khuôn mặt...")
    os.system("python GetDatabase.py")
    print("Hoàn tất lấy dữ liệu khuôn mặt.")

def train_khuonmat():
    """
    Xóa model cũ (nếu có) và chạy script để huấn luyện model mới.
    """
    model_path = "model.yml"
    if os.path.exists(model_path):
        os.remove(model_path)
        print("🗑️ Đã xoá model cũ.")
    
    print("Bắt đầu quá trình train model...")
    os.system("python train.py")
    print("Hoàn tất train model.")

def diemdanh_sinhvien():
    """
    Chạy script điểm danh chính bằng camera.
    """
    print("Khởi động camera để điểm danh...")
    os.system("python main.py")

def quanly_file_lop():
    """
    Hàm này được giữ lại để tương thích, nhưng trong GUI,
    chúng ta nên tạo một cửa sổ riêng để xử lý việc này thay vì dùng input/print.
    """
    print("Chức năng 'Quản lý File Lớp' đã được gọi.")
    print("LƯU Ý: Các thông báo và yêu cầu nhập liệu sẽ hiển thị ở cửa sổ terminal.")
    folder = os.path.join("src", "data-da21ttabc") # Đường dẫn chính xác hơn
    
    # Tạo thư mục nếu chưa tồn tại
    if not os.path.exists(folder):
        os.makedirs(folder)
        print(f"Đã tạo thư mục tại: {folder}")

    files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]
    print("\n📂 Danh sách file lớp hiện có:")
    if not files:
        print("   (Chưa có file nào)")
    else:
        for i, f in enumerate(files, 1):
            print(f"   {i}. {f}")
            
    them = input("\n📥 Bạn có muốn thêm file mới không? (y/n): ")
    if them.lower() == 'y':
        duongdan = input("🔍 Vui lòng kéo và thả file Excel vào đây rồi nhấn Enter, hoặc nhập đường dẫn: ").strip().replace("'", "").replace('"', '')
        if os.path.exists(duongdan) and duongdan.endswith('.xlsx'):
            tenfile = os.path.basename(duongdan)
            try:
                shutil.copy(duongdan, os.path.join(folder, tenfile))
                print(f"✅ Đã thêm thành công file '{tenfile}' vào thư mục lớp.")
            except Exception as e:
                print(f"❌ Đã xảy ra lỗi khi sao chép file: {e}")
        else:
            print("❌ Đường dẫn không hợp lệ hoặc file không phải là file .xlsx.")

def thongke_chitiet_sinhvien():
    """
    Chạy script thống kê chi tiết điểm danh của từng sinh viên.
    """
    print("Bắt đầu chạy thống kê chi tiết...")
    os.system("python thongke.py")

def thongke_theo_ngay():
    """
    Chạy script thống kê điểm danh theo một ngày cụ thể.
    """
    print("Bắt đầu chạy thống kê theo ngày...")
    os.system("python thongke_tungngay.py")

def thongke_nhieu_ngay():
    """
    Chạy script thống kê điểm danh trong một khoảng thời gian.
    """
    print("Bắt đầu chạy thống kê nhiều ngày...")
    os.system("python thongke_nhieungay.py")

# Vòng lặp while True đã được xóa hoàn toàn khỏi file này
# để nó có thể hoạt động như một module cho file MainWindow.py.

# import os

# def laydulieu_khuonmat():
#     os.system("python GetDatabase.py")

# def train_khuonmat():
#     model_path = "model.yml"
#     if os.path.exists(model_path):
#         os.remove(model_path)
#         print("🗑️ Đã xoá model cũ.")
#     os.system("python train.py")

# def diemdanh_sinhvien():
#     os.system("python main.py")


# def quanly_file_lop():
#     folder = "data-da21ttabc"
#     files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]
#     print("📂 Danh sách file lớp hiện có:")
#     for i, f in enumerate(files, 1):
#         print(f"{i}. {f}")
#     them = input("📥 Bạn có muốn thêm file mới không? (y/n): ")
#     if them.lower() == 'y':
#         duongdan = input("🔍 Nhập đường dẫn file Excel cần thêm: ").strip()
#         if os.path.exists(duongdan):
#             tenfile = os.path.basename(duongdan)
#             os.system(f'copy "{duongdan}" "{folder}\\{tenfile}"')
#             print(f"✅ Đã thêm {tenfile} vào thư mục lớp.")
#         else:
#             print("❌ File không tồn tại.")

# def thongke_chitiet_sinhvien():
#     os.system("python thongke.py")

# def thongke_theo_ngay():
#     os.system("python thongke_tungngay.py")

# def thongke_nhieu_ngay():
#     os.system("python thongke_nhieungay.py")
    

# # ===== MENU =====
# while True:
#     print("\n🧠 MENU QUẢN LÝ ĐIỂM DANH KHUÔN MẶT")
#     print("1. Lấy dữ liệu khuôn mặt")
#     print("2. Train dữ liệu khuôn mặt (xoá model cũ)")
#     print("3. Điểm danh sinh viên")
#     print("4. Xem/Thêm file danh sách sinh viên")
#     print("5. Thống kê chi tiết sinh viên")
#     print("6. Thống kê điểm danh theo ngày")
#     print("7. Thống kê điểm danh nhiều ngày")
#     print("0. Thoát")

#     chon = input("👉 Nhập lựa chọn: ").strip()

#     if chon == '1':
#         laydulieu_khuonmat()
#     elif chon == '2':
#         train_khuonmat()
#     elif chon == '3':
#         diemdanh_sinhvien()
#     elif chon == '4':
#         quanly_file_lop()
#     elif chon == '5':
#         thongke_chitiet_sinhvien()
#     elif chon == '6':
#         thongke_theo_ngay()
#     elif chon == '7':
#         thongke_nhieu_ngay()
#     elif chon == '0':
#         print("👋 Thoát chương trình.")
#         break
#     else:
#         print("⚠️ Lựa chọn không hợp lệ. Vui lòng thử lại.")
