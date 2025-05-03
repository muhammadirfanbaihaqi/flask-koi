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


import mysql.connector
from mysql.connector import Error
from urllib.parse import urlparse
# Connection URL yang diberikan oleh Railway
connection_url = "mysql://root:JWWprfxEjxyJCLjIyxKnyoYfdCIjOLFT@caboose.proxy.rlwy.net:30550/railway"

# Mengurai URL untuk mendapatkan detail koneksi
url = urlparse(connection_url)

# Fungsi untuk membuat koneksi
def create_connection():
    try:
        # Mengonfigurasi koneksi menggunakan parameter yang benar
        connection = mysql.connector.connect(
            host=url.hostname,
            user=url.username,
            password=url.password,
            database=url.path[1:],  # Mengambil nama database (tanpa '/')
            port=url.port
        )
        # if connection.is_connected():
        #     st.success("✅ Berhasil konek ke MySQL via Railway")
        return connection
    except Error as e:
        return e

@app.route("/set-jumlah-bukaan", methods=["POST"])
def set_jumlah_bukaan():
    data = request.get_json()
    jumlah = data.get("jumlah_bukaan")
    if jumlah is None or not (1 <= jumlah <= 10):
        return jsonify({"error": "Jumlah bukaan tidak valid"}), 400
    
    # Simpan ke database
        # Membuat koneksi ke database
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE pakan_settings SET jumlah_bukaan = %s WHERE id = 1", (jumlah,))
    conn.commit()
    conn.close()
    return jsonify({"message": "Jumlah bukaan berhasil disimpan"})

@app.route("/get-jumlah-bukaan", methods=["GET"])
def get_jumlah_bukaan():
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT jumlah_bukaan FROM pakan_settings WHERE id = 1")
    result = cursor.fetchone()
    conn.close()
    return jsonify({"jumlah_bukaan": result[0]})


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
    # tz = pytz.timezone('Asia/Jakarta')
    # data_terakhir['timestamp'] = datetime.now(tz)  # tanpa strftime
    data_terakhir['timestamp'] = datetime.now(timezone.utc)
    collection.insert_one(data_terakhir)

    print("📥 Data Diterima:", data_terakhir)
    return jsonify({"message": "Data berhasil disimpan"}), 201


@app.route('/sensor', methods=['GET'])
def ambil_data():
    # Buat salinan supaya data_terakhir asli tidak rusak
    hasil = data_terakhir.copy()
    hasil.pop('_id', None)  # hapus jika ada _id
    return jsonify(hasil), 200




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
    
    # Hapus _id dari setiap dokumen
    for item in data:
        item.pop('_id', None)

    return Response(dumps(data), mimetype='application/json')


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
