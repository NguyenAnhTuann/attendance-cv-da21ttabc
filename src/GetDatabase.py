import cv2
import sqlite3
from unidecode import unidecode
from datetime import datetime
import os.path
import pickle
import threading
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

SCOPES = ['https://www.googleapis.com/auth/drive.file']

# --- Kết nối Google Drive ---
def get_drive_service():
    creds = None
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file('credentials.json', SCOPES)
            creds = flow.run_local_server(port=0)
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)
    return build('drive', 'v3', credentials=creds)

# --- Tạo thư mục con mỗi lần quét ---
def create_upload_folder(folder_name, parent_folder_id):
    service = get_drive_service()
    folder_metadata = {
        'name': folder_name,
        'mimeType': 'application/vnd.google-apps.folder',
        'parents': [parent_folder_id]
    }
    folder = service.files().create(body=folder_metadata, fields='id').execute()
    return folder.get('id')

# --- Upload ảnh lên thư mục con ---
def upload_to_drive(filepath, filename, folder_id):
    service = get_drive_service()
    file_metadata = {'name': filename, 'parents': [folder_id]}
    media = MediaFileUpload(filepath, mimetype='image/jpeg')
    service.files().create(body=file_metadata, media_body=media, fields='id').execute()

    # --- Tìm và xóa folder cũ theo mssv ---
def delete_old_folders(mssv, parent_folder_id):
    service = get_drive_service()
    
    query = f"'{parent_folder_id}' in parents and mimeType='application/vnd.google-apps.folder' and trashed=false and name contains '{mssv}'"
    results = service.files().list(q=query, fields="files(id, name)").execute()
    folders = results.get('files', [])
    
    for folder in folders:
        service.files().delete(fileId=folder['id']).execute()
        print(f"Đã xóa thư mục cũ: {folder['name']}")
        
def delete_local_images(mssv):
    folder_path = 'luu'
    if not os.path.exists(folder_path):
        print("⚠️ Thư mục 'luu' chưa tồn tại.")
        return

    deleted_count = 0
    for filename in os.listdir(folder_path):
        if mssv in filename:
            file_path = os.path.join(folder_path, filename)
            os.remove(file_path)
            deleted_count += 1

    print(f" Đã xóa {deleted_count} file ảnh cũ trong thư mục 'luu' chứa MSSV: {mssv}")



# --- Upload threading ---
def threaded_upload(filepath, filename, folder_id):
    threading.Thread(target=upload_to_drive, args=(filepath, filename, folder_id)).start()


# --- Thêm/Cập nhật sinh viên ---
def AddData(mssv, hoten, ngaysinh, gioitinh, malop):
    conn = sqlite3.connect('../db/attendance.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM sinhvien WHERE mssv = ?", (mssv,))
    isRecordExist = cursor.fetchone()

    if isRecordExist:
        cursor.execute('''
            UPDATE sinhvien
            SET hoten = ?, ngaysinh = ?, gioitinh = ?, malop = ?
            WHERE mssv = ?
        ''', (hoten, ngaysinh, gioitinh, malop, mssv))
    else:
        ngaytao = datetime.now().strftime('%d/%m/%Y')
        cursor.execute('''
            INSERT INTO sinhvien (mssv, hoten, ngaysinh, gioitinh, malop, ngaytao, solantruycap)
            VALUES (?, ?, ?, ?, ?, ?, 0)
        ''', (mssv, hoten, ngaysinh, gioitinh, malop, ngaytao))

    conn.commit()
    conn.close()

# --- Main ---
if __name__ == "__main__":
    # Nhập thông tin sinh viên
    mssv = input('MSSV: ')
    hoten = input('Họ tên: ')
    malop = input('Mã lớp: ')
    ngaysinh = input('Ngày sinh: ')
    gioitinh = input('Giới tính: ')

    hoten_filename = unidecode(hoten).replace(" ", "")
    AddData(mssv, hoten, ngaysinh, gioitinh, malop)

    # Xóa dữ liệu ảnh cũ (cả local và Google Drive)
    parent_folder_id = '1N1OTsq8waQurLzCNG6ZikzO-7x4yScwe'
    delete_old_folders(mssv, parent_folder_id)
    delete_local_images(mssv)

    # Tạo thư mục mới để upload ảnh lần này
    today_str = datetime.now().strftime('%d-%m-%Y')
    folder_name = f"{hoten_filename}.{mssv}-{today_str}"
    sub_folder_id = create_upload_folder(folder_name, parent_folder_id)


    # Camera nhận diện và lưu ảnh
    cam = cv2.VideoCapture(0)
    detector = cv2.CascadeClassifier('haarcascade_frontalface_default.xml')

    lap = 0

    while True:
        ret, img = cam.read()
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        faces = detector.detectMultiScale(gray, 1.3, 5)

        for (x, y, w, h) in faces:
            cv2.rectangle(img, (x, y), (x + w, y + h), (255, 0, 0), 2)
            lap += 1

            filename = f"{hoten_filename}.{mssv}.{lap}.jpg"
            filepath = f"luu/{filename}"
            cv2.imwrite(filepath, gray[y:y+h, x:x+w])

            threaded_upload(filepath, filename, sub_folder_id)

        cv2.imshow('frame', img)

        if cv2.waitKey(100) & 0xFF == ord('q'):
            break
        elif lap >= 20:
            break

    cam.release()
    cv2.destroyAllWindows()

    print("\nĐã lấy dữ liệu khuôn mặt thành công!")
