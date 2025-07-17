import os
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import firebase_admin
from firebase_admin import credentials, firestore
import psutil
from audio_utils.audio_utils import load_audio_full, extract_features, get_file_hash

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

cred = credentials.Certificate('firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
songs_collection = db.collection('songs_scratch')

def log_memory(label):
    mem = psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    print(f"[MEMORY] {label}: {mem:.2f} MB")

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def fetch_songs_from_firestore():
    songs = songs_collection.stream()
    database, features = [], []
    for song in songs:
        data = song.to_dict()
        if "features" in data:
            features.append(data["features"])
            database.append(data)
    return database, features

def get_recommendations(upload_features, db_features, db_songs, exclude_hash=None):
    db_features = np.array(db_features)
    scaler = StandardScaler()
    db_features_norm = scaler.fit_transform(db_features)
    upload_norm = scaler.transform([upload_features])

    similarity_scores = cosine_similarity(upload_norm, db_features_norm)[0]
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

        existing_docs = list(songs_collection.where("file_hash", "==", file_hash).stream())
        if existing_docs:
            print(f"[INFO] Song '{file.filename}' already exists (hash match).")
            upload_features = existing_docs[0].to_dict().get("features")
        else:
            print(f"[INFO] New song '{file.filename}'. Extracting features and uploading to Firestore.")
            upload_features = extract_features(filepath)
            songs_collection.add({
                "filename": file.filename,
                "file_hash": file_hash,
                "features": upload_features,
                "artist": artist,
                "song_name": song_name
            })

        log_memory("After Fetching Songs")
        database, database_features = fetch_songs_from_firestore()

        log_memory("After Upload Feature Extraction")
        recommendations = get_recommendations(upload_features, database_features, database, exclude_hash=file_hash)
        log_memory("After Recommendations")

        return jsonify(recommendations)

    return jsonify({"error": "Invalid file type"}), 400

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
