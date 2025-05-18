# Attendance Face Recognition - DA21TTABC

## 🎯 Giới thiệu
Dự án **Điểm danh lớp DA21TTABC bằng nhận diện khuôn mặt** sử dụng Python và Google Drive API để tự động hóa việc ghi nhận thông tin sinh viên khi tham gia lớp học. Dữ liệu khuôn mặt được lưu trữ cục bộ và đồng bộ lên Google Drive để quản lý tập trung.

## 🛠️ Công nghệ sử dụng
- Python 3.x
- OpenCV (nhận diện khuôn mặt)
- SQLite (cơ sở dữ liệu sinh viên & điểm danh)
- Google Drive API (đồng bộ dữ liệu ảnh)
- Git, GitHub (quản lý phiên bản)
- Visual Studio Code (môi trường phát triển)

## 🗂️ Cấu trúc thư mục
```plaintext
attendance-cv-da21ttabc/
├── .vscode/                         # Cấu hình cho VS Code (nếu cần)
├── db/
│   └── attendance.db                # CSDL SQLite lưu thông tin sinh viên & điểm danh
├── src/
│   ├── __pycache__/                 # Tự động sinh bởi Python (có thể .gitignore)
│   ├── data-da21ttabc/
│   │   └── DA21TTA.xlsx             # File Excel danh sách lớp
│   ├── luu/                         # Thư mục lưu ảnh khuôn mặt đã quét
│   ├── credentials.json             # File chứng thực Google Drive API (bảo mật)
│   ├── token.pickle                 # Token OAuth lưu phiên đăng nhập
│   ├── haarcascade_frontalface_default.xml   # Mô hình Haar cascade nhận diện khuôn mặt
│   ├── label_map.json               # Map ID nhận diện với MSSV
│   ├── model.yml                    # File mô hình nhận diện đã huấn luyện
│   ├── db.py                        # Tương tác DB cơ bản
│   ├── function.py                  # Menu thêm/sửa/xóa sinh viên & điểm danh
│   ├── GetDatabase.py               # Ghi dữ liệu khuôn mặt & upload ảnh lên Google Drive
│   ├── main.py                      # Nhận diện khuôn mặt, điểm danh & lưu thông tin
│   ├── thongke.py                   # Tạo báo cáo thống kê & biểu đồ Excel
│   └── thongke_<mssv>.xlsx          # File kết quả xuất thống kê của sinh viên
├── .gitignore                       # Bỏ qua các file: __pycache__, *.pyc, token.pickle, luu/
├── README.md                        # Hướng dẫn sử dụng & cài đặt (nếu có)

```
## 🚀 Chức năng chính
- ✅ Nhận diện khuôn mặt qua webcam & lưu ảnh
- ✅ Tạo thư mục riêng trên Google Drive theo từng buổi quét
- ✅ Tự động upload ảnh nhận diện lên Google Drive
- ✅ Quản lý thông tin sinh viên trong database SQLite
- ✅ Kiểm tra & xóa dữ liệu khuôn mặt cũ khi quét lại
- ✅ Chống push thông tin nhạy cảm lên GitHub với `.gitignore`

## 📊 Mục tiêu ứng dụng
- Hỗ trợ điểm danh tự động cho lớp DA21TTABC môn Thị giác máy tính.
- Lưu trữ & quản lý dữ liệu nhận diện khuôn mặt đồng bộ.
- Thực hành các kiến thức về thị giác máy tính, API và quản lý dữ liệu.

## ✅ Trạng thái hiện tại
- [x] Quét & lưu ảnh khuôn mặt
- [x] Kết nối Google Drive & upload ảnh
- [x] CSDL SQLite quản lý sinh viên & điểm danh
- [x] Tự động xóa ảnh cũ khi quét lại
- [x] Bảo mật repo (xoá credentials khỏi git)

## 📄 License
Project for study & practice purposes (no commercial use).
