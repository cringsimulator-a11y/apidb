from flask import Flask, request, jsonify
from flask_cors import CORS
import os, json, subprocess, time, signal
import sys

app = Flask(__name__)
CORS(app)

BASE = "data/users"
PROCS = {}

def ensure_server(user):
    base = f"{BASE}/{user}/servers/main"
    os.makedirs(f"{base}/files", exist_ok=True)

    meta = f"{base}/meta.json"
    if not os.path.exists(meta):
        json.dump({"name":"main","created":time.time()}, open(meta,"w"))

    server = f"{base}/server.json"
    if not os.path.exists(server):
        json.dump({
            "env":"python",
            "cpu":1,
            "ram":1,
            "storage":1,
            "running":False,
            "main":"main.py"
        }, open(server,"w"), indent=2)


def jload(p, d=None):
    if not os.path.exists(p): return d
    return json.load(open(p))

def jsave(p, d):
    os.makedirs(os.path.dirname(p), exist_ok=True)
    json.dump(d, open(p,"w"), indent=2)

def user_path(u): return f"{BASE}/{u}"
def server_path(u,s): return f"{BASE}/{u}/servers/{s}"

@app.post("/signup")
def signup():
    d=request.json
    p=f"{user_path(d['username'])}/user.json"
    if os.path.exists(p): return "exists",400
    jsave(p,{"password":d["password"],"credits":200})
    ensure_server(d["username"])
    return {"ok":True}

@app.post("/login")
def login():
    d=request.json
    u=jload(f"{user_path(d['username'])}/user.json")
    if not u or u["password"]!=d["password"]: return "bad",401
    ensure_server(d["username"])
    return {"ok":True}

@app.get("/user/<u>")
def user(u):
    return jload(f"{user_path(u)}/user.json")

@app.get("/servers/<u>")
def servers(u):
    ensure_server(u)
    base=f"{user_path(u)}/servers"
    out=[]
    for s in os.listdir(base):
        meta = jload(f"{base}/{s}/meta.json",{})
        srv  = jload(f"{base}/{s}/server.json",{})
        d = {**meta, **srv}
        d["id"]=s
        out.append(d)
    return out


@app.post("/server/start")
def start():
    d=request.json
    u=d["username"]
    sid=d["server_id"]

    sp=f"{user_path(u)}/servers/{sid}"
    srv=jload(f"{sp}/server.json")

    if srv.get("running"):
        return {"status":"already running"}

    main=srv.get("main","main.py")
    fp=f"{sp}/files/{main}"

    log = open(f"{sp}/runtime.log","a")

    p = subprocess.Popen(
        [sys.executable, srv["main"]],
        cwd=f"{sp}/files",
        stdout=open(f"{sp}/runtime.log","a"),
        stderr=open(f"{sp}/runtime.log","a"),
        creationflags=subprocess.CREATE_NEW_PROCESS_GROUP
    )



    srv["running"]=True
    srv["pid"]=p.pid
    jsave(f"{sp}/server.json", srv)

    return {"status":"started"}




@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/server/stop")
def stop():
    d=request.json
    u=d["username"]
    sid=d["server_id"]

    sp=f"{user_path(u)}/servers/{sid}"
    srv=jload(f"{sp}/server.json")

    pid=srv.get("pid")

    if pid:
        try:
            subprocess.Popen(["taskkill","/PID",str(pid),"/F"])
        except:
            pass

    srv["running"]=False
    srv["pid"]=None
    jsave(f"{sp}/server.json", srv)

    return {"status":"stopped"}



@app.get("/files/<u>/<s>")
def files(u,s):
    ensure_server(u)
    sp=f"{server_path(u,s)}/files"
    out=[]
    for f in os.listdir(sp):
        n,t=f.rsplit(".",1)
        out.append({"name":n,"type":t})
    return out

@app.get("/file/<u>/<s>/<name>")
def get_file(u,s,name):
    p=f"{server_path(u,s)}/files/{name}"
    return {"content":open(p).read()}

@app.post("/file/save")
def save_file():
    d=request.json
    p=f"{server_path(d['username'],d['server_id'])}/files/{d['filename']}"
    open(p,"w").write(d["content"])
    return {"ok":True}

app.run(port=8000)

