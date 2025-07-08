import os
import uuid
import numpy as np
import librosa
import firebase_admin
from firebase_admin import credentials, firestore
from mutagen import File as MutagenFile

# --- Firebase initialization ---
cred = credentials.Certificate("musicgenrediscoverer-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# --- Configuration ---
ROOT_DIR = r"C:\Users\jvess\OneDrive\Documents\UofL Classes\CSE 696\Project"
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac', 'ogg'}
MIN_SIZE_BYTES = 500 * 1024

def is_valid_audio(file_path):
    ext = file_path.split('.')[-1].lower()
    return ext in ALLOWED_EXTENSIONS and os.path.getsize(file_path) >= MIN_SIZE_BYTES

def get_artist_from_metadata(file_path):
    try:
        audio = MutagenFile(file_path, easy=True)
        if audio is None:
            return "Unknown Artist"

        # Tags to try for artist/contributing artist info
        possible_tags = ["contributing artists", "artist", "albumartist", "performer", "composer"]

        for tag in possible_tags:
            if tag in audio:
                artist = audio[tag][0]
                if artist.strip():
                    return artist.strip()

        return "Unknown Artist"
    except Exception as e:
        print(f"Failed to read metadata from {file_path}: {e}")
        return "Unknown Artist"

def extract_features(audio_file):
    try:
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
    except Exception as e:
        print(f"Failed to extract features from {audio_file}: {e}")
        return None

# --- Processing files ---
song_count = 0
for file in os.listdir(ROOT_DIR):
    file_path = os.path.join(ROOT_DIR, file)
    if not os.path.isfile(file_path) or not is_valid_audio(file_path):
        continue

    features = extract_features(file_path)
    if features is None:
        continue

    title = os.path.splitext(file)[0]
    artist = get_artist_from_metadata(file_path)

    song_data = {
        "song_id": str(uuid.uuid4()),
        "song_name": title,
        "artist": artist,
        "features": features,
        "file_name": file
    }

    db.collection("songs_production").add(song_data)
    song_count += 1
    print(f"✅ Uploaded: {artist} - {title}")

print(f"\n✅ Finished uploading {song_count} songs.")
