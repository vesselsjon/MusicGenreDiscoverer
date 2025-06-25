import os
import hashlib
import numpy as np
import librosa
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.preprocessing import StandardScaler
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Firebase
cred = credentials.Certificate(r'./musicgenrediscoverer-firebase-adminsdk.json')
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


@app.route("/MusicGenreDiscoverer/upload", methods=["POST"])
def upload_file():
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

        file_hash = get_file_hash(filepath)

        # Check if song already exists using file hash
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

        # Fetch database songs and features
        database, database_features = fetch_songs_from_firestore()

        # Extract features again for recommendation
        upload_features = extract_features(filepath)

        recommendations = get_recommendations(upload_features, database_features, database, exclude_hash=file_hash)

        return jsonify(recommendations)

    return jsonify({"error": "Invalid file type"}), 400


def extract_features(audio_file):
    y, sr = librosa.load(audio_file, sr=None)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
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


def get_recommendations(upload_features, db_features, db_songs, exclude_hash=None):
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


if __name__ == "__main__":
    app.run(debug=True, port=8080)
