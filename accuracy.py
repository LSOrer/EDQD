from sklearn.cluster import DBSCAN
from datetime import datetime
import numpy as np
from xes_parser import parse_xes 

def check_timestamp_accuracy(log):
    """
    Check if timestamps are within a reasonable range (i.e., no future dates, no dates before 1950-01-01).
    """
    future_timestamps = []
    past_timestamps = []
    now = datetime.now().replace(tzinfo=None) # ensure that all datetime objects have the same timezone awareness
    min_date = datetime(1950, 1, 1)

    for trace in log:
        trace_name = trace['attributes'].get('concept:name', 'Unnamed trace')
        for event in trace['events']:
            timestamp = event.get('time:timestamp')
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp).replace(tzinfo=None)
                if timestamp > now:
                    future_timestamps.append(trace_name)
                if timestamp < min_date:
                    past_timestamps.append(trace_name)

    incorrect_timestamps = {
        'future_timestamps': future_timestamps,
        'past_timestamps': past_timestamps
    }

    return incorrect_timestamps


def jaccard_similarity(list1, list2):
    """
    Calculate the Jaccard similarity between two lists.
    """
    set1, set2 = set(list1), set(list2)
    intersection = len(set1.intersection(set2))
    union = len(set1.union(set2))
    return intersection / union if union != 0 else 0

def cluster_traces_by_events(log, eps=0.5, min_samples=2):
    """
    Cluster traces based on their event sequences to identify traces that might belong to different processes.
    """
    # Extract activity sequences
    trace_sequences = []
    for trace in log:
        events = [event.get('concept:name', '').strip() for event in trace.get('events', []) if 'concept:name' in event]
        trace_sequences.append(events)

    # Calculate pairwise Jaccard similarity
    similarity_matrix = []
    for i in range(len(trace_sequences)):
        row = []
        for j in range(len(trace_sequences)):
            if i == j:
                row.append(1.0)
            else:
                row.append(jaccard_similarity(trace_sequences[i], trace_sequences[j]))
        similarity_matrix.append(row)

    # Convert similarity to distance
    distance_matrix = 1 - np.array(similarity_matrix)

    # Cluster using DBSCAN
    clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
    labels = clustering.fit_predict(distance_matrix)

    # Identify outlier traces
    outlier_traces = []
    for i, label in enumerate(labels):
        if label == -1:  # DBSCAN uses -1 to label outliers
            trace_name = log[i].get('attributes', {}).get('concept:name', f'Trace{i+1}')
            outlier_traces.append(trace_name)

    return outlier_traces




def assess_accuracy(file_path):
    """
    Assess the accuracy of the XES log.
    Returns a dictionary with the assessment results for accuracy.
    """
    try:
        log = parse_xes(file_path)

        timestamp_errors = check_timestamp_accuracy(log)
        outlier_trace_names = cluster_traces_by_events(log)


        return {
            'status': 'success',
            'timestamp_errors': timestamp_errors,
            'potential_traces_of_a_different_process': outlier_trace_names
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    file_path = 'path_to_your_xes_file.xes'
    results = assess_accuracy(file_path)
    print(results)