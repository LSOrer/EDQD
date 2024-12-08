from flask import Flask, request, redirect, render_template, jsonify, url_for
import os
from werkzeug.utils import secure_filename

# import modules for the assessment of each quality dimension
import completeness
import accuracy
import interpretability
import relevancy
import validity

app = Flask(__name__)

# Configurations for local usage
#UPLOAD_FOLDER = '/your-file-path'

# Configurations for Docker usage
UPLOAD_FOLDER = '/app/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the directory exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'xes'}

# Store thresholds in memory (initial default values)
thresholds = {
    "green_main": 100,
    "yellow_main": 80,
    "green_small": 100,
    "yellow_small": 80,
    "pattern_threshold": 1,
    "time_gap_factor_events": 3,
    "time_gap_factor_traces": 2
}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        # Assess the data quality dimensions of the uploaded file
        results = {
            'Completeness' : completeness.assess_completeness(file_path, thresholds),
            'Accuracy' : accuracy.assess_accuracy(file_path),
            'Interpretability': interpretability.assess_interpretability(file_path),
            'Relavency': relevancy.assess_relevancy(file_path),
            'Validity': validity.assess_validity(file_path)
            }
        
        # Remove the temporary file
        os.remove(file_path)

        return jsonify(results)

    return redirect(request.url)

# Route to display threshold settings page
@app.route('/thresholds', methods=['GET'])
def thresholds_page():
    return render_template('thresholds.html', thresholds=thresholds)

# Route to update threshold values
@app.route('/set_thresholds', methods=['POST'])
def set_thresholds():
    thresholds['green_main'] = int(request.form.get('green_main', 100))
    thresholds['yellow_main'] = int(request.form.get('yellow_main', 80))
    thresholds['green_small'] = int(request.form.get('green_small', 100))
    thresholds['yellow_small'] = int(request.form.get('yellow_small', 80))

    thresholds['pattern_threshold'] = float(request.form.get('pattern_threshold', 1))
    thresholds['time_gap_factor_events'] = float(request.form.get('time_gap_factor_events', 3))
    thresholds['time_gap_factor_traces'] = float(request.form.get('time_gap_factor_traces', 2))
    return redirect(url_for('index'))  # Redirect to main page after saving

@app.route('/get_thresholds', methods=['GET'])
def get_thresholds():
    return jsonify(thresholds)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=80, debug=True)
