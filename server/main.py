import os
import hashlib
import numpy as np
import librosa
import psutil
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Firebase
cred = credentials.Certificate(r'firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
songs_collection = db.collection('songs')


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def get_file_hash(filepath):
    """Generate SHA-256 hash of the audio file contents."""
    hasher = hashlib.sha256()
    with open(filepath, 'rb') as f:
        buf = f.read()
        hasher.update(buf)
    return hasher.hexdigest()


def log_memory(stage):
    process = psutil.Process(os.getpid())
    mem = process.memory_info().rss / 1024**2  # Convert to MB
    print(f"[MEMORY] {stage}: {mem:.2f} MB")


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

        existing_docs = songs_collection.where("file_hash", "==", file_hash).stream()
        if any(existing_docs):
            print(f"[INFO] Song '{file.filename}' already exists (hash match).")
        else:
            print(f"[INFO] New song '{file.filename}'. Extracting features and uploading to Firestore.")
            features = extract_features(filepath)
            songs_collection.add({
                "filename": file.filename,
                "file_hash": file_hash,
                "features": features,
                "artist": artist,
                "song_name": song_name
            })

        database, database_features = fetch_songs_from_firestore()
        log_memory("After Fetching Songs")

        upload_features = extract_features(filepath)
        log_memory("After Upload Feature Extraction")

        recommendations = get_recommendations_chunked(upload_features, database_features, database, exclude_hash=file_hash)
        log_memory("After Recommendations")

        return jsonify(recommendations)

    return jsonify({"error": "Invalid file type"}), 400


def extract_features(audio_file):
    log_memory("During librosa.load")
    y, sr = librosa.load(audio_file, sr=None)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=13)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    energy = librosa.feature.rms(y=y)
    zcr = librosa.feature.zero_crossing_rate(y=y)

    feature_vector = np.mean(mfcc, axis=1)
    feature_vector = np.append(feature_vector, tempo)
    feature_vector = np.append(feature_vector, np.mean(chroma, axis=1))
    feature_vector = np.append(feature_vector, np.mean(spectral_centroid, axis=1))
    feature_vector = np.append(feature_vector, np.mean(spectral_rolloff, axis=1))
    feature_vector = np.append(feature_vector, np.mean(energy, axis=1))
    feature_vector = np.append(feature_vector, np.mean(zcr, axis=1))

    return feature_vector.tolist()


def fetch_songs_from_firestore():
    songs = songs_collection.stream()
    database = []
    features = []
    for song in songs:
        data = song.to_dict()
        if "features" in data:
            features.append(data["features"])
            database.append(data)
    return database, features


def get_recommendations_chunked(upload_features, db_features, db_songs, exclude_hash=None, chunk_size=20):
    scaler = StandardScaler()
    upload_norm = scaler.fit_transform([upload_features])[0].reshape(1, -1)

    recommendations = []

    for i in range(0, len(db_features), chunk_size):
        db_chunk = db_features[i:i + chunk_size]
        song_chunk = db_songs[i:i + chunk_size]

        try:
            db_chunk_norm = scaler.transform(db_chunk)
            similarities = cosine_similarity(upload_norm, db_chunk_norm)[0]

            for score, song in zip(similarities, song_chunk):
                if exclude_hash and song.get("file_hash") == exclude_hash:
                    continue
                recommendations.append({
                    "song_name": song.get("song_name", "Unknown"),
                    "artist": song.get("artist", "Unknown"),
                    "score": round(float(score), 6)
                })
        except Exception as e:
            print(f"[WARN] Chunk failed: {e}")

    recommendations.sort(key=lambda x: x["score"], reverse=True)
    return recommendations[:10]


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
