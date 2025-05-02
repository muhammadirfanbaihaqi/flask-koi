from flask import Flask, request, jsonify, Response
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from urllib.parse import quote as url_quote
from datetime import datetime, timedelta, timezone
from bson.json_util import dumps
import pytz

# ===================== KONFIGURASI DASAR =====================
app = Flask(__name__)
CORS(app)
# load_dotenv()

# ===================== KONEKSI MONGODB ======================
MONGO_URI = "mongodb+srv://muhammadirfanbaihaqi538:RgCSSPAItD7lV7Hw@cluster0.rpgtm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["koi"]
collection = db["sensor"]

# ===================== VARIABEL GLOBAL ======================
data_terakhir = {}
jadwal_pakan = [[7, 0], [12, 0], [18, 0]]  # Default jadwal pakan

# ===================== ROUTING UTAMA ========================
@app.route('/')
def home():
    tz = pytz.timezone('Asia/Jakarta')
    current_time = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
    return f"✅ API AIoT Aktif! : {current_time}"

# ================= ENDPOINT SENSOR ================
@app.route('/sensor', methods=['POST'])
def simpan_data():
    global data_terakhir
    data = request.get_json()
    print(data)

    if not data:
        return jsonify({"error": "Tidak ada data yang dikirim"}), 400

    data_terakhir = data
    # Simpan waktu sebagai datetime UTC
    # wib_time = datetime.now(pytz.timezone('Asia/Jakarta'))
    # utc_time = wib_time.astimezone(timezone.utc)
    tz = pytz.timezone('Asia/Jakarta')
    data_terakhir['timestamp'] = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')

    data_terakhir['timestamp'] = data_terakhir
    collection.insert_one(data_terakhir)  # pastikan ini ada diaktifkan lagi
    print("📥 Data Diterima:", data_terakhir)
    return jsonify({"message": "Data berhasil disimpan"}), 201


@app.route('/sensor', methods=['GET'])
def ambil_data():
    return jsonify(data_terakhir), 200


# @app.route('/sensor', methods=['POST'])
# def simpan_data():
#     global data_terakhir
#     data = request.get_json()
    
#     if not data:
#         return jsonify({"error": "Tidak ada data yang dikirim"}), 400
    
#     data_terakhir = data
    # tz = pytz.timezone('Asia/Jakarta')
    # data_terakhir['timestamp'] = datetime.now(tz).strftime('%Y-%m-%d %H:%M:%S')
#     collection.insert_one(data_terakhir)
#     print("📥 Data Diterima:", data_terakhir)
#     return jsonify({"message": "Data berhasil disimpan"}), 201

from flask import request
from datetime import datetime

@app.route('/sensor/history', methods=['GET'])
def ambil_riwayat_data():
    start = request.args.get('start')
    end = request.args.get('end')

    query = {}
    if start and end:
        # Konversi string ke datetime
        try:
            start_dt = datetime.strptime(start, "%Y-%m-%d")
            end_dt = datetime.strptime(end, "%Y-%m-%d") + timedelta(days=1)  # tambah 1 hari agar mencakup seluruh hari "end"
            query["timestamp"] = {"$gte": start_dt, "$lt": end_dt}
        except ValueError:
            return {"error": "Format tanggal tidak valid"}, 400

    data = list(collection.find(query).sort("timestamp", -1).limit(1000))
    return dumps(data), 200

# ================ ENDPOINT JADWAL PAKAN =====================
@app.route('/jadwal_pakan', methods=['GET'])
def get_jadwal():
    return jsonify({"jadwal": jadwal_pakan}), 200

@app.route('/jadwal_pakan', methods=['POST'])
def set_jadwal():
    global jadwal_pakan
    data = request.get_json()

    if not data or "jadwal" not in data or not isinstance(data["jadwal"], list):
        return jsonify({"error": "Jadwal tidak valid"}), 400

    jadwal_baru = [
        [jam, menit] for jam, menit in data["jadwal"]
        if isinstance(jam, int) and isinstance(menit, int)
    ]

    if not jadwal_baru:
        return jsonify({"error": "Format jadwal salah atau kosong"}), 400

    jadwal_pakan = jadwal_baru
    print("🗓️ Jadwal pakan diperbarui:", jadwal_pakan)
    return jsonify({"message": "Jadwal berhasil disimpan"}), 200

# ===================== JALANKAN SERVER ======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
