import cv2
import os
import numpy as np
import sqlite3
import json
import pandas as pd
from datetime import datetime

# ====== CẤU HÌNH ======
model_path = "model.yml"
label_map_path = "label_map.json"

# ====== CHỌN MÔN HỌC ======
mon_list = [
    "Thị Giác Máy Tính",
    "Hệ Thống Thông Tin Quản Lý",
    "Máy Học Ứng Dụng"
]
print("Chọn môn học để điểm danh:")
for i, mon in enumerate(mon_list, 1):
    print(f"{i}. {mon}")
chon = int(input("Nhập số: "))
monhoc = mon_list[chon - 1]

# ====== CHỌN LỚP TỪ FILE EXCEL ======
# ====== CHỌN FILE LỚP TỪ DANH SÁCH TRONG THƯ MỤC ======
folder_path = "data-da21ttabc"
excel_files = [f for f in os.listdir(folder_path) if f.endswith(".xlsx")]

if not excel_files:
    print("❌ Không tìm thấy file Excel trong thư mục.")
    exit()

print("📂 Chọn lớp từ danh sách file:")
for i, filename in enumerate(excel_files, 1):
    print(f"{i}. {filename}")

chon_file = int(input("Nhập số: "))
excel_path = os.path.join(folder_path, excel_files[chon_file - 1])

df_lop = pd.read_excel(excel_path)
print(f"📋 Đã tải lớp từ: {excel_path}, tổng số sinh viên: {len(df_lop)}")


# ====== NHẬP GIỜ BẮT ĐẦU BUỔI HỌC ======
thoigian_buoi_hoc = input("🕗 Nhập thời gian buổi học (hh:mm - hh:mm): ")
start_str, end_str = [t.strip() for t in thoigian_buoi_hoc.split("-")]
start_time = datetime.strptime(start_str, "%H:%M")
end_time = datetime.strptime(end_str, "%H:%M")

# ====== LOAD MÔ HÌNH VÀ MAPPING ======
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(model_path)
with open(label_map_path, 'r') as f:
    id_to_mssv = json.load(f)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cam = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_SIMPLEX
recognized_ids = set()  # để tránh điểm danh trùng

# ====== QUÉT KHUÔN MẶT ======
while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        id_, confidence = recognizer.predict(gray[y:y + h, x:x + w])

        if confidence < 50:
            mssv = id_to_mssv.get(str(id_))
            if mssv and mssv not in recognized_ids:
                recognized_ids.add(mssv)

                now = datetime.now()
                today = now.strftime('%d/%m/%Y')
                current_time = now.strftime('%H:%M:%S')

                # Tính trạng thái vào lớp
                gio_vao = datetime.strptime(current_time[:5], "%H:%M")

                # Nếu đến sau giờ kết thúc -> không cho điểm danh
                if gio_vao > end_time:
                    print(f"⚠ MSSV: {mssv} đến sau giờ kết thúc ({end_str}) ❌ Không điểm danh")
                    continue


                delay = int((gio_vao - start_time).total_seconds() // 60)
                trangthai = "Đúng giờ" if delay <= 0 else f"Trễ {delay} phút"

                # Ghi vào cơ sở dữ liệu
                conn = sqlite3.connect('../db/attendance.db')
                cursor = conn.cursor()

                cursor.execute("SELECT * FROM diemdanh WHERE mssv=? AND ngayhoc=? AND monhoc=?", (mssv, today, monhoc))
                if not cursor.fetchone():
                    cursor.execute(
                        "INSERT INTO diemdanh (mssv, thoigian, ngayhoc, monhoc, trangthaivaolop) VALUES (?, ?, ?, ?, ?)",
                        (mssv, current_time, today, monhoc, trangthai)
                    )
                    print(f"✅ MSSV: {mssv} - {monhoc} - {today} {current_time} ➜ {trangthai}")
                conn.commit()
                conn.close()

            cv2.putText(frame, f"MSSV: {mssv}", (x, y - 10), font, 0.8, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)

        else:
            cv2.putText(frame, "Không nhận diện được!", (x, y - 10), font, 0.8, (0, 0, 255), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imshow('Face Attendance', frame)

    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
