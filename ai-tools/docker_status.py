from flask import Flask, jsonify, request
import subprocess

app = Flask(__name__)

ALLOWED_CONTAINERS = {
    "openwebui",
    "ollama",
    "qdrant",
    "homeassistant",
    "nginx-proxy-manager",
    "portainer",
}

@app.route("/docker/containers")
def containers():
    result = subprocess.run(
        ["docker", "ps", "--format", "{{.Names}} {{.Status}}"],
        capture_output=True,
        text=True
    )
    lines = result.stdout.strip().split("\n")
    containers = []

    for line in lines:
        if line:
            parts = line.split(" ", 1)
            containers.append({
                "name": parts[0],
                "status": parts[1] if len(parts) > 1 else ""
            })

    return jsonify(containers)

@app.route("/docker/logs")
def logs():
    container_name = request.args.get("container")
    lines = request.args.get("lines", default=50, type=int)

    if not container_name:
        return jsonify({"error": "Missing 'container' parameter"}), 400

    if container_name not in ALLOWED_CONTAINERS:
        return jsonify({"error": f"Container '{container_name}' is not allowed"}), 403

    if lines < 1:
        lines = 1
    if lines > 200:
        lines = 200

    result = subprocess.run(
        ["docker", "logs", "--tail", str(lines), container_name],
        capture_output=True,
        text=True
    )

    output = (result.stdout or "") + (result.stderr or "")

    return jsonify({
        "container": container_name,
        "lines": lines,
        "logs": output
    })

app.run(host="0.0.0.0", port=5050)
