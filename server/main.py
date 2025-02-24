from flask import Flask, jsonify, request
from flask_cors import CORS
from pathlib import Path
import implicit
import numpy as np
from musiccollaborativefiltering.data import load_user_artists, ArtistRetriever
from musiccollaborativefiltering.recommender import ImplicitRecommender

app = Flask(__name__)
cors = CORS(app, origins='*')

# Initialize artist retriever
artist_retriever = ArtistRetriever()
artist_retriever.load_artists(Path("hetrec2011-lastfm-2k/artists.dat"))

# Load user artists matrix
user_artists = load_user_artists(Path("hetrec2011-lastfm-2k/user_artists.dat"))

# Instantiate the ALS model using implicit
implicit_model = implicit.als.AlternatingLeastSquares(
    factors=50, iterations=10, regularization=0.01
)

# Instantiate recommender
recommender = ImplicitRecommender(artist_retriever, implicit_model)
recommender.fit(user_artists)

@app.route("/MusicGenreDiscoverer/recommendations", methods=["GET"])
def get_recommendations():
    # Get user ID and number of recommendations from query params
    user_id = int(request.args.get("user_id"))
    n = int(request.args.get("n", 10))
    artists, scores = recommender.recommend(user_id, user_artists, n)

    recommendations = [{"artist": artist, "score": float(score)} for artist, score in zip(artists, scores)]
    return jsonify(recommendations)


if __name__ == "__main__":
    app.run(debug=True, port=8080)
