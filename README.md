# MusicGenreDiscoverer Web App

A music recommendation system that suggests similar songs based on audio feature extraction and machine learning. Built using **Flask** (Python 3.13.2) for the backend and **Angular** (Node v22.13.1, npm 10.9.2) for the frontend, with data stored in **Firebase Firestore**.

---

## Features

- Upload `.mp3`, `.wav`, `.flac`, or `.ogg` songs
- Extracts features using Librosa (tempo, chroma, MFCCs, spectral features)
- Computes similarity using cosine distance
- Stores songs and metadata in Firebase Firestore
- Recommends the 10 most similar songs in the database

---

## Tech Stack

| Layer     | Tech                      |
|-----------|---------------------------|
| Frontend  | Angular (TypeScript)      |
| Backend   | Flask (Python 3.13.2)     |
| Audio     | Librosa, NumPy            |
| ML        | Scikit-learn (cosine sim) |
| Database  | Firebase Firestore        |
| Hosting   | Localhost (`ng serve`)    |

---

## Getting Started

### Prerequisites

Install the following:

- **Python 3.13.2** – [Download](https://www.python.org/downloads/)
- **Node.js v22.13.1 + npm 10.9.2** – [Download](https://nodejs.org/)
- **Firebase Project** – Export your admin SDK key

---

## Python Backend Setup (Flask)

1. **Clone this repository** and navigate to the backend folder
    ```bash
      cd MusicGenreDiscoverer/
      cd server/
    ```
2. Create a virtual environment:
    ```bash
     python -m venv venv
    ```
    activate the venv via this command on Windows:
    ```bash
      venv\Scripts\activate
    ```
    or this command on macOS/Linux
    ```bash
      source venv/bin/activate
    ```
3. Install dependencies:
    ```bash
     pip install flask flask-cors numpy librosa scikit-learn firebase-admin
    ```
4. Add your Firebase Admin SDK JSON as:
    ```bash
      ./musicgenrediscoverer-firebase-adminsdk.json
    ```

    To get this, go into the firebase project settings













   ![image](https://github.com/user-attachments/assets/d7794a71-fa84-4674-b147-99d10358d5b8)

   Then go to the service accounts tab and click generate new key. Once again this will go in the server folder under the name `./musicgenrediscoverer-firebase-adminsdk.json`













   ![image](https://github.com/user-attachments/assets/09b6f388-d1b3-4952-b772-843d1cc6927c)


    
6. Run Flask server:
    ```bash
      python your_flask_file.py
    ```
The backend runs at: `http://localhost:8080`

---

## Frontend Setup (Angular)

1. Navigate to Angular project folder:
    ```bash
      cd client/
    ```
2. Install dependencies:
    ```bash
      npm install
    ```
3. Run Angular development server:
    ```bash
      npm run start
    ```
You can open your browser at: `http://localhost:4200`

---
   
## How to Use

1. Upload a song file from the Angular frontend.
2. Flask backend extracts features using Librosa.
3. Compares uploaded features with database songs using cosine similarity.
4. Returns top 10 similar songs.
5. Angular displays the results.
