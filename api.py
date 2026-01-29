from flask import Flask, request, jsonify
import requests

app = Flask(__name__)

# Your local API URL
LOCAL_API = "https://trying-bow-lottery-giant.trycloudflare.com"

@app.route("/<path:path>", methods=["GET", "POST"])
def proxy(path):
    # Build the URL for the local API
    url = f"{LOCAL_API}/{path}"

    try:
        if request.method == "POST":
            # Forward JSON POST request
            resp = requests.post(url, json=request.get_json(), timeout=10)
        else:
            # Forward GET request
            resp = requests.get(url, params=request.args, timeout=10)
        
        # Return the JSON from local API
        return jsonify(resp.json()), resp.status_code
    except requests.exceptions.RequestException as e:
        return jsonify({"error": "failed to connect to local API", "details": str(e)}), 502

if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
