from flask import Flask, render_template, redirect, url_for, request, flash, Response
import os
import cv2
from GetDatabase import handle_face_capture
import threading

app = Flask(__name__)
app.secret_key = "your_secret_key"  # dùng để hiển thị flash messages

# ---------- TRANG CHỦ ----------
@app.route('/')
def home():
    return render_template('trangchu.html')


# ---------- LẤY DỮ LIỆU KHUÔN MẶT ----------
@app.route('/laydulieu', methods=['GET', 'POST'])
def laydulieu():
    if request.method == 'POST':
        chon = request.form.get('chon')
        try:
            if chon == '1':
                mssv = request.form['mssv_only']
                handle_face_capture(mssv=mssv)
                flash(f"✅ Đã lấy dữ liệu khuôn mặt thành công cho MSSV: {mssv}")
                return render_template("laydulieu_full.html")

            elif chon == '2':
                mssv = request.form['mssv']
                hoten = request.form['hoten']
                ngaysinh = request.form['ngaysinh']
                gioitinh = request.form['gioitinh']
                malop = request.form['malop']
                handle_face_capture(mssv, hoten, ngaysinh, gioitinh, malop)
                flash(f"✅ Đã lấy dữ liệu khuôn mặt cho sinh viên mới: {hoten}")
                return render_template("laydulieu_full.html")

        except ValueError as e:
            flash(str(e))
            return render_template("laydulieu_full.html")

    return render_template("laydulieu_full.html")


# ---------- STREAM VIDEO TỪ CAMERA ----------
# camera = cv2.VideoCapture(0)

camera = None  # Toàn cục

def gen_frames():
    global camera
    if camera is None:
        camera = cv2.VideoCapture(0, cv2.CAP_DSHOW)  # Mở đúng lúc
    while True:
        if camera is None:
            break
        success, frame = camera.read()
        if not success:
            break
        _, buffer = cv2.imencode('.jpg', frame)
        frame = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
        
def gen_frames():
    while True:
        success, frame = camera.read()
        if not success:
            break
        else:
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (
                b'--frame\r\n'
                b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n'
            )

@app.route('/video_feed')
def video_feed():
    return Response(gen_frames(), mimetype='multipart/x-mixed-replace; boundary=frame')


# ---------- CÁC CHỨC NĂNG KHÁC ----------
@app.route('/train', methods=['GET', 'POST'])
def train():
    if request.method == 'POST':
        model_path = "model.yml"
        if os.path.exists(model_path):
            os.remove(model_path)
            print("🗑️ Đã xoá model cũ.")
        os.system("python train.py")
        flash("✅ Đã train lại dữ liệu khuôn mặt thành công.")
        return render_template("train.html")

    return render_template("train.html")

# ---------- ---- ----------
@app.route('/diemdanh', methods=['GET', 'POST'])
def diemdanh():
    folder = "data-da21ttabc"
    excel_files = [f for f in os.listdir(folder) if f.endswith(".xlsx")]

    if request.method == 'POST':
        monhoc = request.form['monhoc']
        filelop = request.form['filelop']
        buoihoc = request.form['buoihoc']
        start_end = {"Sáng": ("07:00", "10:30"), "Chiều": ("13:00", "16:30")}
        start_str, end_str = start_end[buoihoc]

        def run_diemdanh():
            os.environ["MONHOC"] = monhoc
            os.environ["FILELOP"] = filelop
            os.environ["BUOIHOC"] = buoihoc
            os.environ["START"] = start_str
            os.environ["END"] = end_str
            os.system("python diemdanhtheoweb.py")

        threading.Thread(target=run_diemdanh).start()

        return render_template("diemdanh.html", excel_files=excel_files)

    return render_template("diemdanh.html", excel_files=excel_files)

# ---------- ---- ----------

@app.route('/quanly_file_lop')
def quanly_file_lop():
    os.system("python -c 'import function; function.quanly_file_lop()'")
    flash("📁 Đã xử lý file danh sách lớp.")
    return redirect(url_for('home'))

@app.route('/thongke_chitiet')
def thongke_chitiet():
    os.system("python thongke.py")
    return redirect(url_for('home'))

@app.route('/thongke_ngay')
def thongke_ngay():
    os.system("python thongke_tungngay.py")
    return redirect(url_for('home'))

@app.route('/thongke_nhieu_ngay')
def thongke_nhieu_ngay():
    os.system("python thongke_nhieungay.py")
    return redirect(url_for('home'))


# ---------- CHẠY ỨNG DỤNG ----------
if __name__ == '__main__':
    app.run(debug=True)
