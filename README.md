# 🩺 MedAI Assistant — AI-Powered Healthcare Assistant

An AI-powered patient intake and symptom-analysis web app built with **Flask**, **MySQL**, and **OpenAI GPT-4o-mini**. A clinician enters a patient's details and symptoms. The app returns an AI-generated preliminary assessment and saves the case, including the assessment, to a relational database.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)
[![Tests](https://github.com/Bhagya-lekshmi-42/AI-powered-healthcare-assistant/actions/workflows/tests.yml/badge.svg)](https://github.com/Bhagya-lekshmi-42/AI-powered-healthcare-assistant/actions/workflows/tests.yml)

---

## 📌 Project Overview

Front-desk triage often means writing patient details down by hand and waiting for a clinician to make a first pass. **MedAI Assistant** combines both steps:

1. A clean, responsive **Patient Intake Form** captures the patient's name, age, and symptoms, and validates the input.
2. The symptoms are sent to **OpenAI's GPT-4o-mini** with a carefully written system prompt. The model returns a short, empathetic assessment covering possible non-emergency causes, practical next steps, and a clear medical disclaimer.
3. If the symptoms contain **emergency warning signs** (for example chest pain or difficulty breathing), the app shows an urgent-care alert.
4. Each case and its AI assessment are **stored in MySQL**.
5. A **password-protected Patient History Dashboard** lists every recorded case, newest first, with search.

> ⚠️ **Disclaimer:** This is an educational project. The AI output is not medical advice and does not replace a licensed healthcare professional.

---

## ✨ Key Features

- **🧠 AI Symptom Analysis:** OpenAI GPT-4o-mini with a role-based system prompt and low temperature (`0.3`) for consistent, grounded responses.
- **🚨 Emergency Detection:** Flags urgent symptoms and advises the patient to seek immediate care.
- **🗄️ Persistent Records:** Saves each case, its AI assessment, and a timestamp to MySQL using parameterized queries.
- **📊 Patient History Dashboard:** Date, patient details, and expandable AI assessments, with search by name or symptom.
- **🔒 Protected Dashboard:** Patient history requires a clinician password (session-based login).
- **🎨 Modern, Responsive UI:** Consistent Tailwind CSS design across every page.
- **🛡️ Built-in Security:**
  - All output is HTML-escaped by Jinja2 templates, preventing XSS
  - CSRF protection on every form
  - Input validation for name, age, and symptom length
  - Security headers and no-cache headers for sensitive data
  - Friendly error pages that never expose internal details
  - Debug mode off by default
  - The patient's name is **not** sent to the AI, only age and symptoms
- **🧩 Graceful Failure Handling:** If the AI service is unavailable, the case is still saved and the user is told to retry.
- **⚙️ Auto Database Setup:** Creates or upgrades the `patients` table automatically.
- **✅ Automated Tests:** A pytest suite runs on every push with GitHub Actions.

---

## 🛠️ Tech Stack

| Layer          | Technology                                       |
|----------------|--------------------------------------------------|
| **Backend**    | Python, Flask                                    |
| **AI / LLM**   | OpenAI API (`gpt-4o-mini`), Prompt Engineering   |
| **Database**   | MySQL (`mysql-connector-python`)                 |
| **Frontend**   | HTML5, Jinja2 Templates, Tailwind CSS            |
| **Config**     | python-dotenv (environment variables)            |
| **Testing/CI** | pytest, GitHub Actions                           |

---

## 🏗️ How It Works

```
Clinician ──► Intake Form ──POST /submit──► Flask (app.py)
                                              │
                    ┌─────────────────────────┼─────────────────────────┐
                    ▼                         ▼                         ▼
           Validate input          OpenAI GPT-4o-mini          Emergency keyword
                                   (age + symptoms only)            check
                                              │
                                              ▼
                                  MySQL: save case + assessment
                                              │
                                              ▼
                                 Result page (assessment + alerts)

Clinician ──► /login ──► /history (protected) ──► MySQL: list & search cases
```

### Application Routes

| Route      | Method    | Description                                                      |
|------------|-----------|------------------------------------------------------------------|
| `/`        | GET       | Patient intake form                                              |
| `/submit`  | POST      | Validates input, gets the AI assessment, saves the case          |
| `/login`   | GET, POST | Clinician login for the dashboard                                |
| `/history` | GET       | Protected Patient History Dashboard (`?q=` to search)            |
| `/logout`  | POST      | Ends the clinician session                                       |

---

## 📂 Project Structure

```
AI-powered-healthcare-assistant/
├── app.py                   # Flask app: routes, validation, DB, OpenAI integration
├── templates/
│   ├── base.html            # Shared layout (header, footer, Tailwind)
│   ├── index.html           # Patient intake form
│   ├── result.html          # AI assessment result
│   ├── history.html         # Patient History Dashboard
│   ├── login.html           # Clinician login
│   └── error.html           # Friendly error page
├── tests/
│   └── test_app.py          # pytest suite
├── .github/workflows/
│   └── tests.yml            # GitHub Actions CI
├── schema.sql               # Database schema (optional; the app creates it automatically)
├── requirements.txt         # Runtime dependencies
├── requirements-dev.txt     # Runtime + test dependencies
├── .env.example             # Template for environment variables
└── .gitignore
```

---

## ⚙️ Setup Instructions

### Prerequisites

- Python 3.10+
- MySQL Server 8.0+
- An [OpenAI API key](https://platform.openai.com/api-keys)

### 1. Clone the repository

```bash
git clone https://github.com/Bhagya-lekshmi-42/AI-powered-healthcare-assistant.git
cd AI-powered-healthcare-assistant
```

### 2. Create and activate a virtual environment

```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS / Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Create the database

```sql
CREATE DATABASE healthcare_db;
```

The `patients` table is created automatically the first time the app saves a case. You can also run `flask --app app init-db`, or run `schema.sql` manually. Existing tables from older versions are upgraded automatically.

### 5. Configure environment variables

Copy `.env.example` to `.env` and fill in your values:

```env
OPENAI_API_KEY=your_openai_api_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=healthcare_db
SECRET_KEY=a_long_random_string
HISTORY_PASSWORD=choose_a_strong_dashboard_password
```

> Older `.env` files that use `OPEN_API_KEY` still work.

### 6. Run the application

```bash
python app.py
```

Open **http://127.0.0.1:8000** in your browser. Set `FLASK_DEBUG=1` in `.env` only while developing.

---

## ✅ Running Tests

```bash
pip install -r requirements-dev.txt
pytest
```

The tests use mocks, so they need neither a database nor an OpenAI key.

---

## 🚀 Future Enhancements

- Individual clinician accounts with role-based access
- Medical image upload with multimodal AI analysis
- Pagination on the history dashboard
- Export patient reports as PDF
- Deployment with Docker and a cloud-hosted database

---

## 👩‍💻 Author

**Bhagya Lekshmi**
GitHub: [@Bhagya-lekshmi-42](https://github.com/Bhagya-lekshmi-42)

---

⭐ If you found this project interesting, consider giving it a star!
