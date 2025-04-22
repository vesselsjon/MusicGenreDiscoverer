import firebase_admin
from firebase_admin import credentials, firestore
import numpy as np

# Initialize Firebase
cred = credentials.Certificate(r".\musicgenrediscoverer-firebase-adminsdk.json")
firebase_admin.initialize_app(cred)
db = firestore.client()

# Generate dummy data
for i in range(20):  # 20 dummy songs
    features = np.random.rand(37).tolist()  # 37 features
    song_data = {
        "song_id": f"dummy_{i}",
        "song_name": f"Dummy Song {i}",
        "artist": f"Dummy Artist {i}",
        "features": features
    }
    db.collection("songs").add(song_data)

print("✅ Dummy data uploaded!")
