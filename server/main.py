import os
import hashlib
import numpy as np
import soundfile as sf
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import firebase_admin
from firebase_admin import credentials, firestore
import psutil
import resampy

# --- Numba/Librosa Memory Optimization ---
os.environ["NUMBA_CACHE_DIR"] = "/tmp/numba_cache"

# --- Flask App Setup ---
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# --- Firebase Initialization ---
cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
songs_collection = db.collection('songs')

# --- Memory Utility ---
def log_memory(label):
    mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    print(f"[MEMORY] {label}: {mem:.2f} MB")

# --- Utility Functions ---
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_hash(filepath):
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        hasher.update(f.read())
    return hasher.hexdigest()

def load_audio_trimmed(filepath, duration=10, sr=22050):
    y, file_sr = sf.read(filepath, always_2d=False)
    if y.ndim > 1:
        y = y.mean(axis=1)
    if file_sr != sr:
        y = resampy.resample(y, file_sr, sr)
    y = y[:int(duration * sr)]
    return y, sr

# --- Feature Extraction ---
def extract_features(audio_file):
    import librosa  # Delay import to avoid loading unless needed
    y, sr = load_audio_trimmed(audio_file, duration=10)
    log_memory("During audio load")

    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        mfcc = librosa.feature.mfcc(y=y, sr=sr)
        chroma = librosa.feature.chroma_stft(y=y, sr=sr)

        # Reduced feature set to avoid memory overload
        feature_vector = np.mean(mfcc, axis=1)
        feature_vector = np.append(feature_vector, tempo)
        feature_vector = np.append(feature_vector, np.mean(chroma, axis=1))

        return feature_vector.tolist()
    except Exception as e:
        print(f"[ERROR] Feature extraction failed: {e}")
        return []

# --- Firestore Retrieval ---
def fetch_songs_from_firestore():
    songs = songs_collection.stream()
    database, features = [], []
    for song in songs:
        data = song.to_dict()
        if "features" in data:
            features.append(data["features"])
            database.append(data)
    return database, features

# --- Recommendation Logic ---
def get_recommendations(upload_features, db_features, db_songs, exclude_hash=None):
    if not upload_features:
        return []

    all_features = np.vstack([upload_features] + db_features)
    scaler = StandardScaler()
    all_features_norm = scaler.fit_transform(all_features)

    upload_norm = all_features_norm[0].reshape(1, -1)
    db_norm = all_features_norm[1:]
    similarity_scores = cosine_similarity(upload_norm, db_norm)[0]
    sorted_indices = np.argsort(similarity_scores)[::-1]

    recommendations = []
    for idx in sorted_indices:
        db_song = db_songs[idx]
        if exclude_hash and db_song.get("file_hash") == exclude_hash:
            continue
        recommendations.append({
            "song_name": db_song.get("song_name", f"Song {idx}"),
            "artist": db_song.get("artist", "Unknown"),
            "score": round(float(similarity_scores[idx]), 6)
        })
        if len(recommendations) >= 10:
            break
    return recommendations

# --- File Upload Route ---
@app.route("/MusicGenreDiscoverer/upload", methods=["POST"])
def upload_file():
    log_memory("Start Upload")
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    song_name = request.form.get('song_name', file.filename)
    artist = request.form.get('artist', 'Unknown Artist')

    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and allowed_file(file.filename):
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filepath)
        log_memory("After File Save")

        file_hash = get_file_hash(filepath)

        try:
            existing_docs = list(songs_collection.where("file_hash", "==", file_hash).stream())
        except Exception as e:
            return jsonify({"error": f"Firestore error: {str(e)}"}), 500

        if existing_docs:
            print(f"[INFO] Song '{file.filename}' already exists (hash match).")
            upload_features = existing_docs[0].to_dict().get("features")
        else:
            print(f"[INFO] New song '{file.filename}'. Extracting features and uploading to Firestore.")
            upload_features = extract_features(filepath)
            if not upload_features:
                return jsonify({"error": "Feature extraction failed."}), 500
            songs_collection.add({
                "filename": file.filename,
                "file_hash": file_hash,
                "features": upload_features,
                "artist": artist,
                "song_name": song_name
            })

        database, database_features = fetch_songs_from_firestore()
        recommendations = get_recommendations(upload_features, database_features, database, exclude_hash=file_hash)
        log_memory("After Recommendations")

        return jsonify(recommendations)

    return jsonify({"error": "Invalid file type"}), 400

# --- Run App ---
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
