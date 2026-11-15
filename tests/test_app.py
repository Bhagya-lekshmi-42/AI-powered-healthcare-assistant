import datetime

import pytest

import app as medai


@pytest.fixture
def saved():
    return []


@pytest.fixture
def client(monkeypatch, saved):
    medai.app.config["TESTING"] = True
    monkeypatch.setattr(medai, "HISTORY_PASSWORD", "test-password")
    monkeypatch.setattr(
        medai, "save_patient", lambda name, age, symptoms, analysis: saved.append((name, age, symptoms, analysis))
    )
    monkeypatch.setattr(medai, "get_ai_assessment", lambda age, symptoms: ("Rest and drink fluids.", None))
    with medai.app.test_client() as test_client:
        yield test_client


def csrf(client):
    with client.session_transaction() as sess:
        sess["_csrf_token"] = "test-token"
    return "test-token"


def submit(client, **overrides):
    data = {"name": "Asha", "age": "30", "symptoms": "dry cough", "csrf_token": csrf(client)}
    data.update(overrides)
    return client.post("/submit", data=data)


def login(client, password="test-password"):
    return client.post("/login", data={"password": password, "csrf_token": csrf(client)})


def test_home_page_renders_form_with_csrf_token(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"Patient Intake Form" in response.data
    assert b'name="csrf_token"' in response.data


def test_submit_without_csrf_token_is_rejected(client, saved):
    response = client.post("/submit", data={"name": "Asha", "age": "30", "symptoms": "cough"})
    assert response.status_code == 400
    assert saved == []


@pytest.mark.parametrize("age", ["", "abc", "-1", "131"])
def test_invalid_age_shows_error_and_saves_nothing(client, saved, age):
    response = submit(client, age=age)
    assert response.status_code == 400
    assert b"age" in response.data.lower()
    assert saved == []


def test_valid_submission_saves_case_with_ai_analysis(client, saved):
    response = submit(client)
    assert response.status_code == 200
    assert b"Rest and drink fluids." in response.data
    assert saved == [("Asha", 30, "dry cough", "Rest and drink fluids.")]


def test_user_input_is_html_escaped(client):
    response = submit(client, name="<script>alert(1)</script>")
    assert b"<script>alert(1)</script>" not in response.data
    assert b"&lt;script&gt;" in response.data


def test_emergency_symptoms_show_urgent_warning(client):
    response = submit(client, symptoms="Severe chest pain since morning")
    assert b"urgent medical attention" in response.data


def test_ai_failure_still_saves_case(client, saved, monkeypatch):
    monkeypatch.setattr(medai, "get_ai_assessment", lambda age, symptoms: (None, "AI unavailable"))
    response = submit(client)
    assert response.status_code == 200
    assert b"AI unavailable" in response.data
    assert saved[0][3] is None


def test_database_failure_shows_friendly_error_without_details(client, monkeypatch):
    def broken_save(*args):
        raise RuntimeError("secret internal detail")

    monkeypatch.setattr(medai, "save_patient", broken_save)
    response = submit(client)
    assert response.status_code == 500
    assert b"Could not save the case" in response.data
    assert b"secret internal detail" not in response.data


def test_patient_name_is_not_sent_to_ai():
    prompt = medai.build_user_prompt(30, "dry cough")
    assert "Age: 30" in prompt
    assert "dry cough" in prompt
    assert "Name" not in prompt


def test_history_requires_login(client):
    response = client.get("/history")
    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_wrong_password_is_rejected(client):
    response = login(client, password="wrong")
    assert b"Incorrect password" in response.data
    assert client.get("/history").status_code == 302


def test_history_shows_escaped_records_after_login(client, monkeypatch):
    searches = []

    def fake_fetch(search=None):
        searches.append(search)
        return [
            {
                "id": 1,
                "name": "<b>Ravi</b>",
                "age": 40,
                "symptoms": "headache",
                "ai_analysis": "Hydrate and rest.",
                "created_at": datetime.datetime(2026, 1, 5, 10, 30),
            }
        ]

    monkeypatch.setattr(medai, "fetch_patients", fake_fetch)
    assert login(client).status_code == 302
    response = client.get("/history?q=head")
    assert response.status_code == 200
    assert b"&lt;b&gt;Ravi&lt;/b&gt;" in response.data
    assert b"Hydrate and rest." in response.data
    assert b"05 Jan 2026" in response.data
    assert searches == ["head"]


def test_dashboard_locked_when_no_password_configured(client, monkeypatch):
    monkeypatch.setattr(medai, "HISTORY_PASSWORD", None)
    response = client.get("/login")
    assert response.status_code == 503
    assert b"HISTORY_PASSWORD" in response.data


def test_emergency_keyword_detection():
    assert medai.has_emergency_signs("Difficulty breathing at night")
    assert not medai.has_emergency_signs("Mild runny nose")
