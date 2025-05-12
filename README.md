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
attendance-cv-da21ttabc/
├── .vscode/ # Cấu hình VSCode (optional)
├── db/
│ └── attendance.db # Database SQLite lưu thông tin sinh viên & điểm danh
├── src/
│ ├── luu/ # Lưu trữ ảnh khuôn mặt đã quét (ignored by .gitignore)
│ ├── credentials.json # Thông tin OAuth Google Drive API (ignored)
│ ├── token.pickle # Token đăng nhập Google Drive API (ignored)
│ ├── haarcascade_frontalface_default.xml # Mô hình nhận diện khuôn mặt HaarCascade
│ ├── db.py # Quản lý thao tác database
│ ├── GetDatabase.py # Xử lý kết nối Google Drive & upload ảnh
│ └── main.py # Chương trình chính (quét khuôn mặt & upload)
├── .gitignore # Danh sách file/folder không đưa lên git
├── README.md # Tài liệu dự án

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
