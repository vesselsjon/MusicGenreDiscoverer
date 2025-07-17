import os
import uuid
from mutagen import File as MutagenFile
import firebase_admin
from firebase_admin import credentials, firestore
from audio_utils.audio_utils import extract_features, get_file_hash

cred = credentials.Certificate("musicgenrediscoverer-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

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
        for tag in ["contributing artists", "artist", "albumartist", "performer", "composer"]:
            if tag in audio and audio[tag][0].strip():
                return audio[tag][0].strip()
        return "Unknown Artist"
    except Exception as e:
        print(f"Metadata error for {file_path}: {e}")
        return "Unknown Artist"

song_count = 0
for file in os.listdir(ROOT_DIR):
    file_path = os.path.join(ROOT_DIR, file)
    if not os.path.isfile(file_path) or not is_valid_audio(file_path):
        continue

    file_hash = get_file_hash(file_path)
    existing = list(db.collection("songs_scratch").where("file_hash", "==", file_hash).stream())
    if existing:
        print(f"⚠️ Duplicate skipped: {file}")
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
        "file_name": file,
        "file_hash": file_hash
    }

    db.collection("songs_scratch").add(song_data)
    song_count += 1
    print(f"✅ Uploaded: {artist} - {title}")

print(f"\n✅ Finished uploading {song_count} songs.")
