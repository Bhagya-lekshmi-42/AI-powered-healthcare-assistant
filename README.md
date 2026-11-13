# 🩺 MedAI Assistant — AI-Powered Healthcare Assistant

An AI-powered patient intake and symptom-analysis web app built with **Flask**, **MySQL**, and **OpenAI GPT-4o-mini**. Clinicians enter a patient's details and symptoms. The app saves the case to a relational database and returns an AI-generated preliminary assessment within seconds.

![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?logo=python&logoColor=white)
![Flask](https://img.shields.io/badge/Flask-3.0-000000?logo=flask&logoColor=white)
![MySQL](https://img.shields.io/badge/MySQL-8.0-4479A1?logo=mysql&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o--mini-412991?logo=openai&logoColor=white)
![TailwindCSS](https://img.shields.io/badge/Tailwind_CSS-38B2AC?logo=tailwind-css&logoColor=white)

---

## 📌 Project Overview

Front-desk triage often means writing patient details down by hand and waiting for a clinician to make a first pass. **MedAI Assistant** combines both steps:

1. A clean, responsive **Patient Intake Form** captures the patient's name, age, and primary symptom.
2. Each submission is **stored in MySQL**, so every case leaves a record.
3. The symptoms are sent to **OpenAI's GPT-4o-mini** with a carefully written system prompt. The model returns a short, empathetic assessment that covers possible non-emergency causes, practical next steps, and a clear medical disclaimer.
4. A **Patient History Dashboard** lists every recorded case, newest first.

The project shows full-stack skills: backend routing, relational data persistence, LLM integration with prompt engineering, secure configuration, and modern UI design.

> ⚠️ **Disclaimer:** This is an educational project. The AI output is not medical advice and does not replace a licensed healthcare professional.

---

## ✨ Key Features

- **🧠 AI Symptom Analysis:** Uses OpenAI GPT-4o-mini with a role-based system prompt and low temperature (`0.3`) so responses stay consistent and grounded.
- **🗄️ Persistent Patient Records:** Saves every case to a MySQL database using parameterized queries to prevent SQL injection.
- **📊 Patient History Dashboard:** Shows all past cases in a table, sorted from newest to oldest.
- **🎨 Modern, Responsive UI:** A polished intake form built with Tailwind CSS and the Plus Jakarta Sans font that works on desktop and mobile.
- **🔐 Secure Configuration:** API keys and database credentials load from a `.env` file with `python-dotenv` and are kept out of version control by `.gitignore`.
- **🚫 No-Cache Headers:** Every response sets strict `Cache-Control` headers so browsers don't cache sensitive patient data.
- **🛡️ Responsible AI Output:** The prompt makes the model include a disclaimer and tell the patient to seek professional care for severe symptoms.

---

## 🛠️ Tech Stack

| Layer          | Technology                                   |
|----------------|----------------------------------------------|
| **Backend**    | Python, Flask                                |
| **AI / LLM**   | OpenAI API (`gpt-4o-mini`), Prompt Engineering |
| **Database**   | MySQL (`mysql-connector-python`)             |
| **Frontend**   | HTML5, Jinja2 Templates, Tailwind CSS        |
| **Config**     | python-dotenv (environment variables)        |
| **Tools**      | Git, GitHub, VS Code                         |

---

## 🏗️ System Architecture / Workflow

```
┌──────────────────────┐
│   Clinician / User   │
└──────────┬───────────┘
           │ 1. Fills intake form (name, age, symptoms)
           ▼
┌──────────────────────┐        POST /submit
│  Frontend (Tailwind) │ ─────────────────────────┐
│   templates/index    │                          │
└──────────────────────┘                          ▼
                                    ┌──────────────────────────┐
                                    │      Flask Backend       │
                                    │         app.py           │
                                    └─────┬──────────────┬─────┘
              2. INSERT patient record    │              │  3. Send symptoms +
                 (parameterized query)    │              │     system prompt
                                          ▼              ▼
                              ┌────────────────┐  ┌──────────────────┐
                              │  MySQL Database │  │  OpenAI API      │
                              │  healthcare_db  │  │  GPT-4o-mini     │
                              │  └─ patients    │  └────────┬─────────┘
                              └───────┬────────┘           │
                                      │                    │ 4. AI assessment
          GET /history                │                    ▼
   ◄──── 6. Patient History ──────────┘     ┌──────────────────────────┐
         Dashboard (all records)            │ 5. Result page: patient  │
                                            │    details + AI analysis │
                                            └──────────────────────────┘
```

### Application Routes

| Route       | Method | Description                                                      |
|-------------|--------|------------------------------------------------------------------|
| `/`         | GET    | Shows the patient intake form.                                   |
| `/submit`   | POST   | Saves the patient to MySQL, calls OpenAI, and shows the AI assessment. |
| `/history`  | GET    | Shows the Patient History Dashboard with all saved records.      |

---

## 📂 Project Structure

```
AI-powered-healthcare-assistant/
├── app.py                # Flask app: routes, DB connection, OpenAI integration
├── requirements.txt      # Python dependencies
├── templates/
│   ├── index.html        # Patient intake form (Tailwind CSS UI)
│   └── result.html       # AI assessment result template
├── .env                  # Environment variables (not committed)
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
pip install flask openai mysql-connector-python python-dotenv
```

> Or install the full pinned environment with `pip install -r requirements.txt`.

### 4. Set up the MySQL database

Log in to MySQL and run:

```sql
CREATE DATABASE healthcare_db;
USE healthcare_db;

CREATE TABLE patients (
    id        INT AUTO_INCREMENT PRIMARY KEY,
    name      VARCHAR(100) NOT NULL,
    age       INT NOT NULL,
    symptoms  TEXT NOT NULL
);
```

### 5. Configure environment variables

Create a `.env` file in the project root:

```env
OPEN_API_KEY=your_openai_api_key_here
DB_HOST=localhost
DB_USER=root
DB_PASSWORD=your_mysql_password
DB_NAME=healthcare_db
```

### 6. Run the application

```bash
python app.py
```

Open **http://127.0.0.1:8000** in your browser.

---

## 🚀 Future Enhancements

- Clinician authentication and role-based access to patient records
- Medical image upload with multimodal AI analysis
- Search, filtering, and pagination on the history dashboard
- Export patient reports as PDF
- Deployment with Docker and a cloud-hosted database

---

## 👩‍💻 Author

**Bhagya Lekshmi**
GitHub: [@Bhagya-lekshmi-42](https://github.com/Bhagya-lekshmi-42)

---

⭐ If you found this project interesting, consider giving it a star!
