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

def find_duplicate_events(log):
    """
    Find and handle duplicate events within the same trace.
    Returns a list of trace names where duplicate events have occurred.
    """
    duplicate_events_in_trace = []

    for trace in log:
        trace_name = trace.get('attributes', {}).get('concept:name', 'Unnamed trace')
        event_set = set()
        duplicates_found = False

        for event in trace.get('events', []):
            # Convert event dictionary to a frozenset of key-value tuples for immutability and comparison
            event_frozenset = frozenset(event.items())
            
            if event_frozenset in event_set:
                duplicates_found = True
            else:
                event_set.add(event_frozenset)

        if duplicates_found:
            duplicate_events_in_trace.append(trace_name)

    return duplicate_events_in_trace

def find_duplicate_traces(log):
    """
    Find and handle duplicate traces.
    Returns a list of trace names where duplicate traces have occurred.
    """
    duplicate_trace_names = set()  # Use a set to avoid duplicate entries
    trace_set = set()
    trace_to_name_map = {}

    for trace in log:
        trace_name = trace.get('attributes', {}).get('concept:name', 'Unnamed trace')
        # Convert trace events to a tuple of frozensets for immutability and comparison
        trace_events = tuple(frozenset(event.items()) for event in trace.get('events', []))

        if trace_events in trace_set:
            duplicate_trace_names.add(trace_name)  # Add duplicate trace name
            duplicate_trace_names.add(trace_to_name_map[trace_events])  # Add the original trace name
        else:
            trace_set.add(trace_events)
            trace_to_name_map[trace_events] = trace_name

    return list(duplicate_trace_names)

def assess_accuracy(file_path):
    """
    Assess the accuracy of the XES log.
    Returns a dictionary with the assessment results for accuracy.
    """
    try:
        log = parse_xes(file_path)

        timestamp_errors = check_timestamp_accuracy(log)
        outlier_trace_names = cluster_traces_by_events(log)
        duplicate_events = find_duplicate_events(log)
        duplicate_traces = find_duplicate_traces(log)


        return {
            'status': 'success',
            'timestamp_errors': timestamp_errors,
            'potential_traces_of_a_different_process': outlier_trace_names,
            'duplicate_events_in_trace' : duplicate_events,
            'duplicate_traces' : duplicate_traces
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