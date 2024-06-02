from flask import Flask, request, jsonify
from flask_cors import CORS
from werkzeug.utils import secure_filename

import os
import completeness
import accuracy

import time_gaps
from xes_parser import parse_xes

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
        results = {
            'Completeness' : completeness.assess_completeness(file_path),
            'Accuracy' : accuracy.assess_accuracy(file_path)
            }
        
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

@app.route('/api/event-timegaps', methods=['POST'])
def event_timegaps():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        log = parse_xes(file_path)
        time_gap_factor = 3.2  # Example factor, you may want to make this configurable
        time_gap_indices, info = time_gaps.analyze_event_time_gaps(log, time_gap_factor)
        
        time_gap_anomalies = []
        for index in time_gap_indices:
            if index < len(log) - 1:
                trace_name = log[index]['attributes'].get('concept:name', 'Unnamed trace')
                time_gap_anomalies.append(trace_name)
        
        response = {
            "significant_traces": time_gap_anomalies,
            "info": info
        }
        
        # Remove the temporary file
        os.remove(file_path)

        return jsonify(response), 200

@app.route('/api/inter-trace-gaps', methods=['POST'])
def inter_trace_gaps():
    if 'file' not in request.files:
        return jsonify({"error": "No file part in the request"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file:
        filename = secure_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        log = parse_xes(file_path)
        time_gap_factor = 2  # Example factor, you may want to make this configurable
        significant_gaps, mean_gap = time_gaps.analyze_inter_trace_gaps(log, time_gap_factor)
        
        response = {
            "significant_gaps": significant_gaps,
            "mean_gap": mean_gap
        }
        
        # Remove the temporary file
        os.remove(file_path)

        return jsonify(response), 200


def assess_data_quality(log):
    # Example assessment, replace with actual logic
    dimensions = ['Completeness', 'Accuracy', 'Consistency']
    scores = [90, 85, 88]
    return {'dimensions': dimensions, 'scores': scores}

if __name__ == '__main__':
    app.run(debug=True)