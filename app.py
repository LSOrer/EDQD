from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import os
import completeness

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}})

UPLOAD_FOLDER = '/Users/babettebaier/Desktop/EDQD/logs'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/api/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'})

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No selected file'})

    # Save the uploaded file to a temporary location
    filename = secure_filename(file.filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
    file.save(file_path)

    try:
        # Assess the completeness of the uploaded file
        results = completeness.assess_completeness(file_path)
        
        # Remove the temporary file
        os.remove(file_path)
        
        return jsonify(results)
    
    except Exception as e:
        # Capture any exceptions and print for debugging
        print("Error processing file:", str(e))
        
        # Ensure temporary file is removed in case of error
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return jsonify({'error': 'Error processing file', 'message': str(e)})

def assess_data_quality(log):
    # Example assessment, replace with actual logic
    dimensions = ['Completeness', 'Accuracy', 'Consistency']
    scores = [90, 85, 88]
    return {'dimensions': dimensions, 'scores': scores}

if __name__ == '__main__':
    app.run(debug=True)