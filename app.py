"""
EduGenie - Flask routes for the Gemini-powered learning assistant.

Architecture:
    Browser (HTML/CSS/JS)
        -> Flask routes (app.py)
            -> gemini_client.py
                -> Google Gemini API
"""

import os

from dotenv import load_dotenv
from flask import Flask, jsonify, render_template, request

import gemini_client
from gemini_client import GeminiError

load_dotenv()

app = Flask(__name__)

# Populated at import time so both `python app.py` and a WSGI server work.
MODEL_NAME = None
try:
    MODEL_NAME = gemini_client.configure()
except GeminiError as exc:
    print(f"Gemini not configured: {exc}")
    print("The UI will load, but AI features will return an error.")


# --------------------------------------------------------------------------
# Feature handlers, one per route. Each returns the JSON key the frontend reads.
# --------------------------------------------------------------------------

def _payload():
    """Read the JSON body and return the 'input' field as a string."""
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return ""
    value = data.get("input", "")
    if not isinstance(value, str):
        return ""
    return value.strip()


def _run(feature, builder):
    """Shared plumbing: validate input, call Gemini, format the response."""
    if MODEL_NAME is None:
        return jsonify({
            "error": "Gemini is not configured. Set GEMINI_API_KEY in your .env "
                     "file, then restart the server."
        }), 503

    user_input = _payload()
    if not user_input:
        return jsonify({"error": "Please enter some text first."}), 400

    try:
        answer = gemini_client.generate(MODEL_NAME, feature, user_input)
    except GeminiError as exc:
        return jsonify({"error": str(exc)}), 502

    return jsonify({"result": builder(answer), "model": MODEL_NAME})


@app.route("/")
def home():
    return render_template("index.html", model=MODEL_NAME)


@app.route("/ask", methods=["POST"])
def ask():
    return _run("ask", lambda answer: {"answer": answer})


@app.route("/summarize", methods=["POST"])
def summarize():
    return _run("summarize", lambda answer: {"summary": answer})


@app.route("/quiz", methods=["POST"])
def quiz():
    return _run("quiz", lambda answer: {"quiz": answer})


@app.route("/health")
def health():
    """Lets the frontend confirm the API key is configured before first use."""
    return jsonify({"status": "ok", "model": MODEL_NAME})


# --------------------------------------------------------------------------
# Error handling: always reply with JSON so the frontend never parses an HTML
# error page.
# --------------------------------------------------------------------------

@app.errorhandler(404)
def not_found(_exc):
    return jsonify({"error": "Endpoint not found."}), 404


@app.errorhandler(405)
def bad_method(_exc):
    return jsonify({"error": "Method not allowed."}), 405


@app.errorhandler(500)
def server_error(_exc):
    return jsonify({"error": "Something went wrong on the server."}), 500


if __name__ == "__main__":
    debug = os.getenv("FLASK_DEBUG", "0") == "1"
    if MODEL_NAME:
        print(f"Gemini ready. Model: {MODEL_NAME}")
    port = int(os.getenv("PORT", "5000"))
    host = os.getenv("HOST", "127.0.0.1")
    print(f"Starting EduGenie on http://{host}:{port}")
    app.run(host=host, port=port, debug=debug)
