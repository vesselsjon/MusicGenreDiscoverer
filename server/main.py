import os
import librosa
import numpy as np
from flask import Flask, jsonify, request
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity

import firebase_admin
from firebase_admin import credentials, firestore

# Flask setup
app = Flask(__name__)
CORS(app, origins='*')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Firebase setup
cred = credentials.Certificate("path/to/serviceAccountKey.json")  # <-- replace with your path
firebase_admin.initialize_app(cred)
db = firestore.client()

# Utils
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# API Endpoint
@app.route("/MusicGenreDiscoverer/upload", methods=["POST"])
def upload_file():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400
    
    if file and allowed_file(file.filename):
        filename = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
        file.save(filename)

        # Extract audio features
        features = extract_features(filename)

        # Optionally save this song in Firestore
        db.collection('songs').add({
            "song_name": file.filename,
            "artist": "Uploaded by User",
            "features": features
        })

        # Fetch all existing songs in Firestore for similarity comparison
        docs = db.collection('songs').stream()
        database = []
        database_features = []

        for doc in docs:
            data = doc.to_dict()
            if "features" in data:
                database.append({
                    "song_name": data.get("song_name", "Unknown"),
                    "artist": data.get("artist", "Unknown")
                })
                database_features.append(data["features"])

        # Generate and return recommendations
        recommendations = get_recommendations(features, database_features, database)
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

def get_recommendations(features, database_features, database):
    similarity_scores = cosine_similarity([features], database_features)
    sorted_indices = np.argsort(similarity_scores[0])[::-1]

    recommendations = []
    for idx in sorted_indices[:10]:
        recommendations.append({
            "song_id": idx,
            "score": round(similarity_scores[0][idx], 3),
            "song_name": database[idx]["song_name"],
            "artist": database[idx]["artist"]
        })

    return recommendations

if __name__ == "__main__":
    app.run(debug=True, port=8080)
