from flask import Flask, render_template, request 
app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')
@app.route('/submit', methods=['POST'])
def submit():
    patient_name = request.form.get('name')
    patient_age = request.form.get('age')
    patient_symptoms = request.form.get('symptoms')

    return f"""
    <h3>Form Submitted Successfully!</h3>
    <p><b>Name:</b> {patient_name}</p>
    <p><b>Age:</b> {patient_age}</p>
    <p><b>Symptoms:</b> {patient_symptoms}</p>
    <a href="/">Go Back</a>
    """
if __name__== '__main__':
    app.run(debug=True)
