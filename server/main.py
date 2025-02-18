from flask import Flask, jsonify
from flask_cors import CORS

app = Flask(__name__)
cors = CORS(app, origins='*')

@app.route("/MusicGenreDiscoverer/users", methods=['GET'])
def users():
    return jsonify(
        {
            "users": [
                'jon',
                'jacob',
                'emi',
                'doc',
                'blake',
                'ryan',
            ]
        }
    )

if __name__ == "__main__":
    app.run(debug=True, port=8080)