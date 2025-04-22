import os
import numpy as np
import librosa
from flask import Flask, request, jsonify
from flask_cors import CORS
from sklearn.metrics.pairwise import cosine_similarity
import firebase_admin
from firebase_admin import credentials, firestore

# Initialize Flask app
app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

# Initialize Firebase
cred = credentials.Certificate(r'.\musicgenrediscoverer-firebase-adminsdk.json')
firebase_admin.initialize_app(cred)
db = firestore.client()
songs_collection = db.collection('songs')


# Helper to check allowed file types
def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# Route to upload audio file and get recommendations
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

        # Check for duplicates in Firestore by filename
        existing_docs = songs_collection.where("filename", "==", file.filename).stream()
        if any(existing_docs):
            print("Song already exists in Firestore.")
        else:
            print("New song. Extracting features and uploading to Firestore.")
            features = extract_features(filename)

            # Save to Firestore
            songs_collection.add({
                "filename": file.filename,
                "features": features,
                "artist": "Unknown Artist",
                "song_name": file.filename
            })

        # Fetch database for recommendations
        database, database_features = fetch_songs_from_firestore()
        features = extract_features(filename)
        recommendations = get_recommendations(features, database_features, database)

        return jsonify(recommendations)

    return jsonify({"error": "Invalid file type"}), 400


# Extract audio features using librosa
def extract_features(audio_file):
    y, sr = librosa.load(audio_file, sr=None)

    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)
    spectral_centroid = librosa.feature.spectral_centroid(y=y, sr=sr)
    spectral_rolloff = librosa.feature.spectral_rolloff(y=y, sr=sr)
    energy = librosa.feature.rms(y=y)
    zcr = librosa.feature.zero_crossing_rate(y=y)

    # Combine features
    feature_vector = np.mean(mfcc, axis=1)
    feature_vector = np.append(feature_vector, tempo)
    feature_vector = np.append(feature_vector, np.mean(chroma, axis=1))
    feature_vector = np.append(feature_vector, np.mean(spectral_centroid, axis=1))
    feature_vector = np.append(feature_vector, np.mean(spectral_rolloff, axis=1))
    feature_vector = np.append(feature_vector, np.mean(energy, axis=1))
    feature_vector = np.append(feature_vector, np.mean(zcr, axis=1))

    return feature_vector.tolist()


# Fetch all stored songs from Firestore
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


# Content-based recommendation using cosine similarity
def get_recommendations(features, database_features, database):
    similarity_scores = cosine_similarity([features], database_features)
    sorted_indices = np.argsort(similarity_scores[0])[::-1]

    recommendations = []
    for idx in sorted_indices[:10]:
        recommendations.append({
            "song_name": database[idx].get("song_name", f"Song {idx}"),
            "artist": database[idx].get("artist", "Unknown"),
            "score": round(float(similarity_scores[0][idx]), 2)
        })
    return recommendations


if __name__ == "__main__":
    app.run(debug=True, port=8080)
