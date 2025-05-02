
from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi 
import os
import mysql.connector
# api_flask.py
import numpy as np
from PIL import Image
from io import BytesIO
from ultralytics import YOLO
import cv2
from datetime import datetime
from bson.json_util import dumps
from bson.objectid import ObjectId

app = Flask(__name__)
CORS(app)

from dotenv import load_dotenv
load_dotenv()

# Koneksi ke MySQL Railway
def get_db_connection():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST"),
        port=int(os.getenv("DB_PORT")),
        user=os.getenv("DB_USER"),
        password=os.getenv("DB_PASSWORD"),
        database=os.getenv("DB_NAME")
    )

def init_db():
    # conn = get_db_connection()
    # cursor = conn.cursor()
    # cursor.execute('''
    #     CREATE TABLE IF NOT EXISTS jadwal_pakan (
    #         id INT AUTO_INCREMENT PRIMARY KEY,
    #         waktu_pakan TIME NOT NULL,
    #         jumlah_pakan INT NOT NULL,
    #         hari VARCHAR(20) NOT NULL
    #     )
    # ''')
    # conn.commit()
    # cursor.close()
    # conn.close()
    print("✅ Tabel 'jadwal_pakan' sudah dipastikan ada.")


# URI MongoDB
uri = "mongodb+srv://muhammadirfanbaihaqi538:9bS08vSHwy07ETmY@cluster0.rpgtm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"

# Membuat klien baru dan menghubungkan ke server MongoDB
client = MongoClient(uri, server_api=ServerApi('1'))

# Memilih database "iot_db" di dalam MongoDB
db = client["iot_db"]

# Memilih koleksi "SIC6_COLLECTION" untuk menyimpan data sensor
collection = db["suhu"]

# ================= DATA SEMENTARA =================
data_terakhir = {}
jadwal_pakan = [[7, 0], [12, 0], [18, 0]]  # Default: 3x sehari

# ================= ROUTING UTAMA =================
@app.route('/')
def home():
    return "✅ API AIoT Aktif!"

# Load YOLOv8 model
model = YOLO("models/best (2).pt")  # Ganti dengan path model kamu

@app.route('/detect', methods=['POST'])
def detect_fish():
    try:
        # Ambil file gambar dari request
        file = request.files['image']
        image = Image.open(file).convert("RGB")

        # Konversi gambar ke format OpenCV (BGR)
        img_array = np.array(image)
        img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

        # Deteksi menggunakan YOLOv8
        results = model(img_bgr)
        num_fish = len(results[0].boxes)

        # Menghasilkan gambar hasil deteksi
        result_img = results[0].plot()

        # Simpan hasil deteksi gambar sebagai byte
        is_success, buffer = cv2.imencode(".jpg", result_img)
        result_img_bytes = buffer.tobytes()

        return jsonify({
            "num_fish": num_fish,
            "image": result_img_bytes.hex()  # Mengirimkan gambar dalam bentuk hex string
        })

    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ================= ENDPOINT SENSOR ================
# @app.route('/sensor', methods=['POST'])
# def simpan_data():
#     global data_terakhir
#     data = request.get_json()
#     print(data)

#     if not data:
#         return jsonify({"error": "Tidak ada data yang dikirim"}), 400

#     data_terakhir = data
#     print("📥 Data Diterima:", data_terakhir)
#     return jsonify({"message": "Data berhasil disimpan"}), 201

# @app.route('/sensor', methods=['GET'])
# def ambil_data():
#     return jsonify(data_terakhir), 200

@app.route('/sensor', methods=['POST'])
def simpan_data():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Tidak ada data yang dikirim"}), 400

    data['timestamp'] = datetime.utcnow()
    collection.insert_one(data)
    return jsonify({"message": "Data berhasil disimpan"}), 201

@app.route('/sensor', methods=['GET'])
def ambil_data_terbaru():
    data = collection.find().sort("timestamp", -1).limit(1)
    return dumps(data[0]), 200


@app.route('/sensor/history', methods=['GET'])
def ambil_riwayat_data():
    data = list(collection.find().sort("timestamp", -1).limit(1000))
    return dumps(data), 200


# =============== ENDPOINT JADWAL PAKAN ===============
@app.route('/jadwal_pakan', methods=['GET'])
def get_jadwal():
    return jsonify({"jadwal": jadwal_pakan}), 200

@app.route('/jadwal_pakan', methods=['POST'])
def set_jadwal():
    global jadwal_pakan
    data = request.get_json()

    if not data or "jadwal" not in data or not isinstance(data["jadwal"], list):
        return jsonify({"error": "Jadwal tidak valid"}), 400

    jadwal_baru = []
    for item in data["jadwal"]:
        if isinstance(item, list) and len(item) == 2:
            jam, menit = item
            if isinstance(jam, int) and isinstance(menit, int):
                jadwal_baru.append([jam, menit])
    
    if not jadwal_baru:
        return jsonify({"error": "Format jadwal salah atau kosong"}), 400

    jadwal_pakan = jadwal_baru
    print("🗓️ Jadwal pakan diperbarui:", jadwal_pakan)
    return jsonify({"message": "Jadwal berhasil disimpan"}), 200

# ================= RUN SERVER =================
if __name__ == '__main__':
    init_db()
    app.run(host='0.0.0.0', port=5000, debug=True)
