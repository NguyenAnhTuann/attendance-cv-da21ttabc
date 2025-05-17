import cv2
import os
import numpy as np
import json

dataset_path = "luu"
faces = []
labels = []
mssv_to_id = {}
id_to_mssv = {}
current_id = 0

for filename in os.listdir(dataset_path):
    if filename.endswith(".jpg"):
        mssv = filename.split(".")[1]
        if mssv not in mssv_to_id:
            mssv_to_id[mssv] = current_id
            id_to_mssv[current_id] = mssv
            current_id += 1

        img_path = os.path.join(dataset_path, filename)
        img = cv2.imread(img_path, cv2.IMREAD_GRAYSCALE)
        faces.append(img)
        labels.append(mssv_to_id[mssv])

# Train LBPH
recognizer = cv2.face.LBPHFaceRecognizer_create()
recognizer.train(faces, np.array(labels))
recognizer.save("model.yml")

# Lưu map id -> mssv
with open("label_map.json", "w") as f:
    json.dump(id_to_mssv, f)

print("✅ Đã huấn luyện và lưu mô hình, mapping id-mssv.")
