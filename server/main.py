import os
import uuid
import hashlib
import psutil
import librosa
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from google.cloud import firestore
from werkzeug.utils import secure_filename
from scipy.signal import resample

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ALLOWED_EXTENSIONS = {'mp3', 'wav', 'ogg'}

# Initialize Firestore
db = firestore.Client()
songs_collection = db.collection('songs')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def hash_file(filepath):
    hasher = hashlib.md5()
    with open(filepath, 'rb') as afile:
        buf = afile.read()
        hasher.update(buf)
    return hasher.hexdigest()

def log_memory(tag):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / (1024 * 1024)
    print(f"[MEMORY] {tag}: {mem:.2f} MB")

def extract_features(audio_file):
    log_memory("Before librosa.load")
    y, sr = librosa.load(audio_file, sr=None, mono=True, duration=30)
    if sr > 22050:
        duration = y.shape[0] / sr
        new_len = int(22050 * duration)
        y = resample(y, new_len)
        sr = 22050
    log_memory("After librosa.load")

    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_bandwidth = librosa.feature.spectral_bandwidth(y=y, sr=sr)
    rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    zero_crossing_rate = librosa.feature.zero_crossing_rate(y)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)

    features = np.hstack([
        np.mean(chroma), np.std(chroma),
        np.mean(spectral_centroid), np.std(spectral_centroid),
        np.mean(spectral_bandwidth), np.std(spectral_bandwidth),
        np.mean(rolloff), np.std(rolloff),
        np.mean(zero_crossing_rate), np.std(zero_crossing_rate),
        np.mean(mfcc), np.std(mfcc)
    ])

    return features.tolist()

def recommend_songs(features, top_k=5):
    log_memory("Before Recommendation Query")
    songs = list(songs_collection.stream())
    log_memory("After Firestore Query")

    recommendations = []
    for song in songs:
        data = song.to_dict()
        if 'features' not in data:
            continue
        dist = np.linalg.norm(np.array(features) - np.array(data['features']))
        recommendations.append((dist, data))

    recommendations.sort(key=lambda x: x[0])
    return [rec[1] for rec in recommendations[:top_k]]

@app.route('/MusicGenreDiscoverer/upload', methods=['POST'])
def upload_file():
    log_memory("Start Upload")
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400

    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        filepath = os.path.join(UPLOAD_FOLDER, str(uuid.uuid4()) + '_' + filename)
        file.save(filepath)
        log_memory("After File Save")

        file_hash = hash_file(filepath)
        existing_docs = list(songs_collection.where("file_hash", "==", file_hash).stream())

        if existing_docs:
            print(f"[INFO] Song '{filename}' already exists (hash match).")
            existing_data = existing_docs[0].to_dict()
            features = existing_data['features']
        else:
            print(f"[INFO] New song '{filename}'. Extracting features and uploading to Firestore.")
            features = extract_features(filepath)
            log_memory("After Upload Feature Extraction")
            songs_collection.add({
                'filename': filename,
                'file_hash': file_hash,
                'features': features
            })

        recommended = recommend_songs(features)
        log_memory("After Recommendations")
        return jsonify({'recommendations': recommended})

    return jsonify({'error': 'Invalid file'}), 400

if __name__ == '__main__':
    app.run(debug=False, host='0.0.0.0', port=10000)