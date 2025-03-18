import librosa
import numpy as np
import os
from flask import Flask, jsonify, request
from flask_cors import CORS
from pydub import AudioSegment

app = Flask(__name__)
cors = CORS(app, origins='*')

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}

# Create uploads folder if it doesn't exist
if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

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

        # Extract features from the audio file
        features = extract_features(filename)

        # Here you would perform classification and recommendations
        recommendations = get_recommendations(features)

        return jsonify(recommendations)
    
    return jsonify({"error": "Invalid file type"}), 400

def extract_features(audio_file):
    """
    Function to extract features from the audio file using librosa and pydub.
    This is a basic example, you can extend it to extract more features like MFCC, Spectrogram, etc.
    """
    # Load the audio file using librosa
    y, sr = librosa.load(audio_file, sr=None)

    # Extract some basic features
    tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
    chroma = librosa.feature.chroma_stft(y=y, sr=sr)
    mfcc = librosa.feature.mfcc(y=y, sr=sr)

    # Example: Combine some features
    feature_vector = np.mean(mfcc, axis=1)  # Mean MFCC over time
    feature_vector = np.append(feature_vector, tempo)  # Add tempo as a feature
    feature_vector = np.append(feature_vector, np.mean(chroma, axis=1))  # Mean chroma

    return feature_vector.tolist()

def get_recommendations(features):
    """
    Placeholder for your content-based recommendation logic.
    In this example, you will classify the genre based on features and return similar tracks.
    """
    # For now, return dummy recommendations (you would plug in your actual ML model here)
    recommendations = [
        {"artist": "Artist 1", "genre": "Pop", "score": 0.95},
        {"artist": "Artist 2", "genre": "Pop", "score": 0.89},
        {"artist": "Artist 3", "genre": "Rock", "score": 0.85}
    ]
    return recommendations

if __name__ == "__main__":
    app.run(debug=True, port=8080)
