from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo.mongo_client import MongoClient
from pymongo.server_api import ServerApi
from dotenv import load_dotenv

import os
import numpy as np
from PIL import Image
from io import BytesIO
import cv2
from datetime import datetime
from bson.json_util import dumps
import pytz

# ===================== KONFIGURASI DASAR =====================
app = Flask(__name__)
CORS(app)
load_dotenv()

# ===================== KONEKSI MONGODB ======================
MONGO_URI = "mongodb+srv://muhammadirfanbaihaqi538:RgCSSPAItD7lV7Hw@cluster0.rpgtm.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
client = MongoClient(MONGO_URI, server_api=ServerApi('1'))
db = client["koi"]
collection = db["sensor"]

# ===================== VARIABEL GLOBAL ======================
data_terakhir = {}
jadwal_pakan = [[7, 0], [12, 0], [18, 0]]  # Default jadwal pakan



tz = pytz.timezone('Asia/Jakarta')
current_time = datetime.now(tz)
print(f"✅ API AIoT Aktif! : {current_time}")
