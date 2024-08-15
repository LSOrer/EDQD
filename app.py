from flask import Flask, request, redirect, render_template, jsonify
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
#UPLOAD_FOLDER = '/directory_of_this_code/logs'

# Configurations for Docker usage
UPLOAD_FOLDER = '/app/uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)  # Ensure the directory exists
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

ALLOWED_EXTENSIONS = {'xes'}

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
            'Completeness' : completeness.assess_completeness(file_path),
            'Accuracy' : accuracy.assess_accuracy(file_path),
            'Interpretability': interpretability.assess_interpretability(file_path),
            'Relavency': relevancy.assess_relevancy(file_path),
            'Validity': validity.assess_validity(file_path)
            }
        
        # Remove the temporary file
        os.remove(file_path)

        return jsonify(results)

    return redirect(request.url)

if __name__ == '__main__':
    #app.run(debug=True)
    app.run(host="0.0.0.0", port=80, debug=True)