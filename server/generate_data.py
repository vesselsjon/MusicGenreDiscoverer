import os
import numpy as np
import librosa
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase initialization
cred = credentials.Certificate(r".\musicgenrediscoverer-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Constants
ROOT_DIR = r"D:\osu!\Songs"
ALLOWED_EXTENSIONS = {'mp3', 'wav', 'flac'}
MIN_SIZE_BYTES = 500 * 1024

def is_valid_audio(file_path):
    ext = file_path.split('.')[-1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        return False
    if os.path.getsize(file_path) < MIN_SIZE_BYTES:
        return False
    return True

def extract_song_metadata(folder_name):
    try:
        parts = folder_name.split(' ', 1)
        beatmap_id = parts[0]
        artist_title = parts[1].split(' - ')
        if len(artist_title) == 2:
            artist, title = artist_title
        else:
            artist, title = "Unknown", parts[1]
        return beatmap_id, artist.strip(), title.strip()
    except Exception:
        return None, "Unknown", "Unknown"

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

        # Combine features
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

# Upload valid songs
song_count = 0
for folder in os.listdir(ROOT_DIR):
    folder_path = os.path.join(ROOT_DIR, folder)
    if not os.path.isdir(folder_path):
        continue
    if "Various Artists" in folder:
        continue

    for file in os.listdir(folder_path):
        file_path = os.path.join(folder_path, file)
        if not os.path.isfile(file_path):
            continue
        if not is_valid_audio(file_path):
            continue

        beatmap_id, artist, title = extract_song_metadata(folder)
        features = extract_features(file_path)
        if features is None:
            continue

        song_data = {
            "song_id": f"{beatmap_id}_{song_count}",
            "song_name": title,
            "artist": artist,
            "features": features,
            "file_name": file,
            "folder_name": folder
        }
        db.collection("songs").add(song_data)
        song_count += 1
        print(f"Uploaded: {artist} - {title}")
        break

print(f"\nFinished uploading {song_count} songs!")
