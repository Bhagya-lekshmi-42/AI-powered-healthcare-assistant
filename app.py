from flask import Flask, render_template, request
import mysql.connector 

app = Flask(__name__)

def get_db_connection():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",          
        password="***REMOVED***",  
        database="healthcare_db"
    )
    return conn

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/submit', methods=['POST'])
def submit():
    patient_name = request.form.get('name')
    patient_age = request.form.get('age')
    patient_symptoms = request.form.get('symptoms')

    try:
        conn = get_db_connection()
        cur = conn.cursor()
        
        query = "INSERT INTO patients (name, age, symptoms) VALUES (%s, %s, %s)"
        values = (patient_name, int(patient_age), patient_symptoms)
        cur.execute(query, values)
        
        conn.commit()
        
        cur.close()
        conn.close()

        return f"""
        <h3>Data Saved Successfully to MySQL Table!</h3>
        <p><b>Name:</b> {patient_name}</p>
        <p><b>Age:</b> {patient_age}</p>
        <p><b>Symptoms:</b> {patient_symptoms}</p>
        <a href="/">Go Back</a>
        """
        
    except Exception as e:
        return f"<h3>An error occurred: {e}</h3>"

if __name__== '__main__':
    app.run(debug=True)
