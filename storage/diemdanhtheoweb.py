import os
import cv2
import numpy as np
import sqlite3
import json
import pandas as pd
from datetime import datetime

# ==== Nhận dữ liệu từ Flask thông qua biến môi trường ====
monhoc = os.environ.get("MONHOC")
filelop = os.environ.get("FILELOP")
buoihoc = os.environ.get("BUOIHOC")
start_str = os.environ.get("START")
end_str = os.environ.get("END")

if not (monhoc and filelop and buoihoc):
    print("❌ Thiếu thông tin để điểm danh.")
    exit()

folder_path = "data-da21ttabc"
excel_path = os.path.join(folder_path, filelop)
df_lop = pd.read_excel(excel_path)
print(f"📋 Lớp: {filelop} - Sĩ số: {len(df_lop)} | Môn: {monhoc} | Buổi: {buoihoc}")

start_time = datetime.strptime(start_str, "%H:%M")
end_time = datetime.strptime(end_str, "%H:%M")

# ==== Load model và labels ====
model_path = "model.yml"
label_map_path = "label_map.json"
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.read(model_path)

with open(label_map_path, 'r') as f:
    id_to_mssv = json.load(f)

face_cascade = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')
cam = cv2.VideoCapture(0)
font = cv2.FONT_HERSHEY_SIMPLEX
recognized_ids = set()

print("🔍 Bắt đầu điểm danh bằng webcam... Nhấn Q để kết thúc.")

while True:
    ret, frame = cam.read()
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    faces = face_cascade.detectMultiScale(gray, 1.3, 5)

    for (x, y, w, h) in faces:
        id_, confidence = recognizer.predict(gray[y:y+h, x:x+w])
        if confidence < 50:
            mssv = id_to_mssv.get(str(id_))
            if mssv and mssv not in recognized_ids:
                recognized_ids.add(mssv)

                now = datetime.now()
                today = now.strftime('%d/%m/%Y')
                current_time = now.strftime('%H:%M:%S')
                gio_vao = datetime.strptime(current_time[:5], "%H:%M")

                if gio_vao > end_time:
                    print(f"⚠ MSSV: {mssv} đến sau giờ kết thúc ({end_str}) ❌ Không điểm danh")
                    continue

                delay = int((gio_vao - start_time).total_seconds() // 60)
                trangthai = "Đúng giờ" if delay <= 0 else f"Trễ {delay} phút"

                conn = sqlite3.connect('db/attendance.db')
                cursor = conn.cursor()

                # Kiểm tra đã điểm danh chưa
                cursor.execute("""
                    SELECT * FROM diemdanh
                    WHERE mssv=? AND ngayhoc=? AND monhoc=? AND buoihoc=?
                """, (mssv, today, monhoc, buoihoc))
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO diemdanh (mssv, thoigian, ngayhoc, monhoc, trangthaivaolop, buoihoc)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (mssv, current_time, today, monhoc, trangthai, buoihoc))
                    print(f"✅ MSSV: {mssv} - {monhoc} - {today} {current_time} ➜ {trangthai} ({buoihoc})")
                else:
                    print(f"⚠ MSSV: {mssv} đã điểm danh buổi {buoihoc} hôm nay.")
                conn.commit()
                conn.close()

            cv2.putText(frame, f"MSSV: {mssv}", (x, y - 10), font, 0.8, (0, 255, 0), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
        else:
            cv2.putText(frame, "Unknow!", (x, y - 10), font, 0.8, (0, 0, 255), 2)
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 0, 255), 2)

    cv2.imshow('🔍 Hệ thống điểm danh TVU', frame)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cam.release()
cv2.destroyAllWindows()
print("📷 Kết thúc điểm danh.")
