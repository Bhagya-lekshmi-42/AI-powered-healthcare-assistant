from flask import Flask, render_template, request, redirect, url_for
import mysql.connector 
import os
from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

app = Flask(__name__)

@app.after_request
def add_header(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '-1'
    return response

client = OpenAI(api_key=os.environ.get("OPEN_API_KEY"))

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

        system_instruction = (
            "You are an expert AI Healthcare Assistant. Analyze the patient's symptoms provided. "
            "Provide a brief, empathetic response containing: 1. Potential non-emergency causes, "
            "2. Practical next-steps or home care advice, and 3. A clear disclaimer that you are an AI, "
            "not a doctor, and they should seek medical help for severe symptoms."
        )
        user_prompt = f"Patient Name: {patient_name}\nAge: {patient_age}\nSymptoms: {patient_symptoms}"
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  
            messages=[
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.3
        )
        ai_analysis = response.choices[0].message.content

        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 800px; margin: auto; padding: 20px;">
            <div style="background-color: white; padding: 30px; border-radius: 8px; box-shadow: 0 4px 8px rgba(0,0,0,0.1); border: 1px solid #ddd;">
                <h3 style="color: #2c3e50; margin-top: 0;">Data Saved and Analyzed Successfully!</h3>
                <p><b>Patient Name:</b> {patient_name}</p>
                <p><b>Age:</b> {patient_age}</p>
                <p><b>Submitted Symptoms:</b> {patient_symptoms}</p>
                <hr style="border: 0; border-top: 1px solid #eee; margin: 20px 0;">
                
                <h4 style="color: #2c3e50;">🤖 AI Medical Assessment (OpenAI):</h4>
                <div style="background-color: #f0f4f8; padding: 20px; border-radius: 5px; white-space: pre-wrap; border-left: 5px solid #3498db; line-height: 1.6; color: #333;">
                    {ai_analysis}
                </div>
                <br><br>
                
                <!-- ബട്ടണുകൾ ഇവിടെ നൽകുന്നു -->
                <a href="/" style="background-color: #7f8c8d; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; margin-right: 10px; display: inline-block; font-weight: bold;">Go Back</a>
                
                <a href="/history" style="background-color: #3498db; color: white; padding: 12px 24px; text-decoration: none; border-radius: 4px; display: inline-block; font-weight: bold;">📊 View Patient History Dashboard</a>
            </div>
        </div>
        """
        
    except Exception as e:
        return f"<h3>An error occurred: {e}</h3>"
    
@app.route('/history')
def history():
    try:
        conn = get_db_connection()
        cur = conn.cursor(dictionary=True) 
        cur.execute("SELECT * FROM patients ORDER BY id DESC") 
        patients = cur.fetchall()
        cur.close()
        conn.close()
        
        table_rows = ""
        for p in patients:
            table_rows += f"""
            <tr>
                <td style="padding: 10px; border: 1px solid #ddd;">{p['id']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p['name']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p['age']}</td>
                <td style="padding: 10px; border: 1px solid #ddd;">{p['symptoms']}</td>
            </tr>
            """
            
        return f"""
        <div style="font-family: Arial, sans-serif; max-width: 1000px; margin: auto; padding: 20px;">
            <h3 style="color: #2c3e50;">📋 Patient History Dashboard</h3>
            <table style="width: 100%; border-collapse: collapse; margin-top: 20px;">
                <thead>
                    <tr style="background-color: #f2f2f2;">
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">ID</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Name</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Age</th>
                        <th style="padding: 10px; border: 1px solid #ddd; text-align: left;">Symptoms</th>
                    </tr>
                </thead>
                <tbody>
                    {table_rows if table_rows else '<tr><td colspan="4" style="text-align:center; padding:10px;">No records found.</td></tr>'}
                </tbody>
            </table>
            <br><br>
            <a href="/" style="background-color: #34495e; color: white; padding: 10px 20px; text-decoration: none; border-radius: 5px; display: inline-block;">Go Back to Home</a>
        </div>
        """
    except Exception as e:
        return f"<h3>An error occurred while fetching history: {e}</h3>"

if __name__== '__main__':
    app.run(debug=True, port=8000)
