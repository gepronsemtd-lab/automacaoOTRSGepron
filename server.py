import os
import hmac
import subprocess
import sys
from flask import Flask, request, session, redirect, send_from_directory, jsonify
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__, static_folder="dist")
app.secret_key = os.getenv("DASHBOARD_SECRET_KEY")

DASHBOARD_PORT = 5001
DASHBOARD_USER = os.getenv("DASHBOARD_USER")
DASHBOARD_PASS = os.getenv("DASHBOARD_PASS")

if not all([app.secret_key, DASHBOARD_USER, DASHBOARD_PASS]):
    raise RuntimeError(
        "DASHBOARD_SECRET_KEY, DASHBOARD_USER e DASHBOARD_PASS precisam estar definidos."
    )

def autenticado():
    return session.get("auth") is True

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = request.form.get("user", "")
        password = request.form.get("password", "")

        user_ok = hmac.compare_digest(user, DASHBOARD_USER or "")
        pass_ok = hmac.compare_digest(password, DASHBOARD_PASS or "")

        if user_ok and pass_ok:
            session["auth"] = True
            return redirect("/")

        return "Usuário ou senha inválidos", 401

    return """
    <form method="post">
      <h1>Entrar</h1>
      <input name="user" placeholder="Usuário" autocomplete="username">
      <input name="password" type="password" placeholder="Senha" autocomplete="current-password">
      <button type="submit">Entrar</button>
    </form>
    """

@app.route("/logout")
def logout():
    session.clear()
    return redirect("/login")

@app.route("/sync", methods=["POST"])
def sync():
    if not autenticado():
        return jsonify({"error": "Não autorizado"}), 401

    try:
        subprocess.run([sys.executable, "main.py"], check=True)
        return jsonify({"ok": True})
    except subprocess.CalledProcessError:
        return jsonify({"error": "Falha ao gerar dashboard"}), 500

@app.route("/")
def index():
    if not autenticado():
        return redirect("/login")

    return send_from_directory("dist", "index.html")

@app.route("/assets/<path:path>")
def assets(path):
    if not autenticado():
        return redirect("/login")

    return send_from_directory("dist/assets", path)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=DASHBOARD_PORT)
