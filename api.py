from flask import Flask, request, jsonify
import os, json, secrets

app = Flask(__name__)

BASE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(BASE, "data")
USERS = os.path.join(BASE, "users.json")
APIKEYS = os.path.join(BASE, "apikeys.json")

ADMIN_KEYS = ["MASTER_KEY_123"]

os.makedirs(DATA, exist_ok=True)

def load(path):
    if not os.path.exists(path):
        with open(path, "w") as f:
            f.write("{}")
        return {}
    try:
        with open(path, "r") as f:
            return json.load(f)
    except:
        with open(path, "w") as f:
            f.write("{}")
        return {}

def save(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=2)

@app.route("/admin", methods=["POST"])
def admin():
    d = request.json
    if d.get("adminkey") not in ADMIN_KEYS:
        return jsonify({"error":"unauthorized"}),403

    users = load(USERS)
    keys = load(APIKEYS)
    action = d.get("action")

    if action == "create_apikey":
        k = secrets.token_hex(16)
        keys[k] = True
        save(APIKEYS, keys)
        return jsonify({"apikey": k})

    if action == "add_apikey":
        keys[d["apikey"]] = True
        save(APIKEYS, keys)

    elif action == "remove_apikey":
        keys.pop(d["apikey"], None)
        save(APIKEYS, keys)

    elif action == "add_user":
        if d["apikey"] not in keys:
            return jsonify({"error":"apikey not valid"}),400
        users[d["login"]] = {
            "password": d["password"],
            "apikey": d["apikey"]
        }
        save(USERS, users)

    elif action == "remove_user":
        users.pop(d["login"], None)
        save(USERS, users)

    elif action == "get_users":
        return jsonify(users)

    elif action == "get_apikeys":
        return jsonify(keys)

    else:
        return jsonify({"error":"invalid action"}),400

    return jsonify({"status":"ok"})

@app.route("/set", methods=["POST"])
def setval():
    d = request.json
    users = load(USERS)
    keys = load(APIKEYS)

    login = d.get("login")
    password = d.get("password")
    apikey = d.get("apikey")

    if apikey not in keys:
        return jsonify({"error":"apikey invalid"}),403

    if login not in users:
        return jsonify({"error":"login invalid"}),403

    if users[login]["password"] != password:
        return jsonify({"error":"password invalid"}),403

    if users[login]["apikey"] != apikey:
        return jsonify({"error":"apikey not assigned to user"}),403

    base = os.path.join(DATA, apikey, d["name"])
    os.makedirs(base, exist_ok=True)

    location = d.get("location")
    if location:
        base = os.path.join(base, location)
        os.makedirs(base, exist_ok=True)

    path = os.path.join(base, "data.json")
    content = load(path)

    content[d["key"]] = d["value"]
    save(path, content)

    return jsonify({"status":"saved"})

@app.route("/get", methods=["POST"])
def getval():
    d = request.json
    base = os.path.join(DATA, d["apikey"], d["name"])

    location = d.get("location")
    if location:
        base = os.path.join(base, location)

    path = os.path.join(base, "data.json")
    if not os.path.exists(path):
        return jsonify({})

    return jsonify(load(path))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
