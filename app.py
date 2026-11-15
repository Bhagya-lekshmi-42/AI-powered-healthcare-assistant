import logging
import os
import secrets
from functools import wraps

import mysql.connector
from dotenv import load_dotenv
from flask import Flask, abort, redirect, render_template, request, session, url_for
from openai import OpenAI

load_dotenv()

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY") or secrets.token_hex(32),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)

OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")
HISTORY_PASSWORD = os.environ.get("HISTORY_PASSWORD")

MAX_NAME_LENGTH = 100
MAX_SYMPTOMS_LENGTH = 1000
MAX_AGE = 130
HISTORY_LIMIT = 200

SYSTEM_INSTRUCTION = (
    "You are an expert AI Healthcare Assistant. Analyze the patient's symptoms provided. "
    "Provide a brief, empathetic response containing: 1. Potential non-emergency causes, "
    "2. Practical next-steps or home care advice, and 3. A clear disclaimer that you are an AI, "
    "not a doctor, and they should seek medical help for severe symptoms."
)

EMERGENCY_KEYWORDS = (
    "chest pain",
    "difficulty breathing",
    "shortness of breath",
    "can't breathe",
    "cannot breathe",
    "unconscious",
    "fainted",
    "seizure",
    "stroke",
    "severe bleeding",
    "coughing blood",
    "vomiting blood",
    "suicidal",
    "slurred speech",
    "face drooping",
)

_openai_client = None


def get_openai_client():
    global _openai_client
    if _openai_client is None:
        api_key = os.environ.get("OPENAI_API_KEY") or os.environ.get("OPEN_API_KEY")
        _openai_client = OpenAI(api_key=api_key)
    return _openai_client


def get_db_connection():
    return mysql.connector.connect(
        host=os.environ.get("DB_HOST", "localhost"),
        user=os.environ.get("DB_USER", "root"),
        password=os.environ.get("DB_PASSWORD"),
        database=os.environ.get("DB_NAME", "healthcare_db"),
    )


def init_db():
    """Create the patients table, or add columns missing from an older version of it."""
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                """
                CREATE TABLE IF NOT EXISTS patients (
                    id          INT AUTO_INCREMENT PRIMARY KEY,
                    name        VARCHAR(100) NOT NULL,
                    age         INT NOT NULL,
                    symptoms    TEXT NOT NULL,
                    ai_analysis TEXT NULL,
                    created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            cur.execute(
                "SELECT COLUMN_NAME FROM information_schema.COLUMNS "
                "WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'patients'"
            )
            existing = {row[0].lower() for row in cur.fetchall()}
            if "ai_analysis" not in existing:
                cur.execute("ALTER TABLE patients ADD COLUMN ai_analysis TEXT NULL")
            if "created_at" not in existing:
                cur.execute(
                    "ALTER TABLE patients ADD COLUMN created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
                )
            conn.commit()
        finally:
            cur.close()
    finally:
        conn.close()


_db_ready = False


def ensure_db():
    global _db_ready
    if not _db_ready:
        init_db()
        _db_ready = True


def save_patient(name, age, symptoms, ai_analysis):
    ensure_db()
    conn = get_db_connection()
    try:
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO patients (name, age, symptoms, ai_analysis) VALUES (%s, %s, %s, %s)",
                (name, age, symptoms, ai_analysis),
            )
            conn.commit()
            return cur.lastrowid
        finally:
            cur.close()
    finally:
        conn.close()


def fetch_patients(search=None):
    ensure_db()
    conn = get_db_connection()
    try:
        cur = conn.cursor(dictionary=True)
        try:
            query = "SELECT id, name, age, symptoms, ai_analysis, created_at FROM patients"
            params = []
            if search:
                query += " WHERE name LIKE %s OR symptoms LIKE %s"
                like = f"%{search}%"
                params = [like, like]
            query += " ORDER BY id DESC LIMIT %s"
            params.append(HISTORY_LIMIT)
            cur.execute(query, params)
            return cur.fetchall()
        finally:
            cur.close()
    finally:
        conn.close()


def build_user_prompt(age, symptoms):
    # The patient's name is deliberately left out: the AI does not need it.
    return f"Age: {age}\nSymptoms: {symptoms}"


def get_ai_assessment(age, symptoms):
    """Return (analysis, error_message). Exactly one of the two is None."""
    try:
        response = get_openai_client().chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_INSTRUCTION},
                {"role": "user", "content": build_user_prompt(age, symptoms)},
            ],
            temperature=0.3,
            timeout=30,
        )
        return (response.choices[0].message.content or "").strip(), None
    except Exception:
        logger.exception("OpenAI request failed")
        return None, "The AI assessment is temporarily unavailable. The case was saved, so please try again later."


def has_emergency_signs(symptoms):
    text = symptoms.lower()
    return any(keyword in text for keyword in EMERGENCY_KEYWORDS)


def validate_patient_form(form):
    name = (form.get("name") or "").strip()
    age_raw = (form.get("age") or "").strip()
    symptoms = (form.get("symptoms") or "").strip()
    errors = []

    if not name:
        errors.append("Please enter the patient's name.")
    elif len(name) > MAX_NAME_LENGTH:
        errors.append(f"Name must be {MAX_NAME_LENGTH} characters or fewer.")

    age = None
    try:
        age = int(age_raw)
        if not 0 <= age <= MAX_AGE:
            errors.append(f"Age must be between 0 and {MAX_AGE}.")
    except ValueError:
        errors.append("Please enter a valid age in years.")

    if not symptoms:
        errors.append("Please describe the symptoms.")
    elif len(symptoms) > MAX_SYMPTOMS_LENGTH:
        errors.append(f"Symptoms must be {MAX_SYMPTOMS_LENGTH} characters or fewer.")

    return {"name": name, "age": age, "age_raw": age_raw, "symptoms": symptoms}, errors


def get_csrf_token():
    if "_csrf_token" not in session:
        session["_csrf_token"] = secrets.token_urlsafe(32)
    return session["_csrf_token"]


app.jinja_env.globals["csrf_token"] = get_csrf_token


@app.before_request
def csrf_protect():
    if request.method == "POST":
        expected = session.get("_csrf_token")
        submitted = request.form.get("csrf_token", "")
        if not expected or not secrets.compare_digest(expected, submitted):
            abort(400)


@app.after_request
def add_security_headers(response):
    response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
    response.headers["Pragma"] = "no-cache"
    response.headers["Expires"] = "-1"
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "same-origin"
    return response


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if not session.get("authenticated"):
            return redirect(url_for("login"))
        return view(*args, **kwargs)

    return wrapped


@app.route("/")
def home():
    return render_template("index.html", form={}, errors=[])


@app.route("/submit", methods=["POST"])
def submit():
    form, errors = validate_patient_form(request.form)
    if errors:
        return render_template("index.html", form=form, errors=errors), 400

    analysis, ai_error = get_ai_assessment(form["age"], form["symptoms"])

    try:
        save_patient(form["name"], form["age"], form["symptoms"], analysis)
    except Exception:
        logger.exception("Saving patient failed")
        return render_template(
            "error.html",
            title="Could not save the case",
            message="The database is not reachable right now. Please check the database settings and try again.",
        ), 500

    return render_template(
        "result.html",
        name=form["name"],
        age=form["age"],
        symptoms=form["symptoms"],
        analysis=analysis,
        ai_error=ai_error,
        emergency=has_emergency_signs(form["symptoms"]),
    )


@app.route("/login", methods=["GET", "POST"])
def login():
    if not HISTORY_PASSWORD:
        return render_template("login.html", disabled=True, error=None), 503

    error = None
    if request.method == "POST":
        password = request.form.get("password", "")
        if secrets.compare_digest(password, HISTORY_PASSWORD):
            session.clear()
            session["authenticated"] = True
            return redirect(url_for("history"))
        error = "Incorrect password. Please try again."
    return render_template("login.html", disabled=False, error=error)


@app.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("home"))


@app.route("/history")
@login_required
def history():
    search = (request.args.get("q") or "").strip()[:MAX_NAME_LENGTH]
    try:
        patients = fetch_patients(search or None)
    except Exception:
        logger.exception("Fetching patient history failed")
        return render_template(
            "error.html",
            title="Could not load patient history",
            message="The database is not reachable right now. Please try again later.",
        ), 500
    return render_template("history.html", patients=patients, search=search)


@app.errorhandler(400)
def bad_request(_error):
    return render_template(
        "error.html",
        title="Request could not be processed",
        message="Your session may have expired. Please go back, refresh the page and try again.",
    ), 400


@app.errorhandler(404)
def not_found(_error):
    return render_template(
        "error.html", title="Page not found", message="The page you are looking for does not exist."
    ), 404


@app.cli.command("init-db")
def init_db_command():
    """Create or upgrade the patients table."""
    init_db()
    print("Database is ready.")


if __name__ == "__main__":
    app.run(debug=os.environ.get("FLASK_DEBUG") == "1", port=int(os.environ.get("PORT", 8000)))
