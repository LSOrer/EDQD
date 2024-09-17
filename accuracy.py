from sklearn.cluster import DBSCAN
from datetime import datetime
import numpy as np
from xes_parser import parse_xes 

def check_timestamp_accuracy(log):
    """
    Check if timestamps are within a reasonable range (i.e., no future dates, no dates before 1980-01-01).
    """
    future_timestamps = []
    past_timestamps = []
    now = datetime.now().replace(tzinfo=None) # ensure that all datetime objects have the same timezone awareness
    min_date = datetime(1980, 1, 1)

    for trace in log:
        trace_name = trace['attributes'].get('concept:name', 'Unnamed trace')
        for event in trace['events']:
            timestamp = event.get('time:timestamp')
            event_name = event.get('concept:name', 'Unnamed event')
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp).replace(tzinfo=None)
                if timestamp > now:
                    future_timestamps.append((trace_name, event_name))
                if timestamp < min_date:
                    past_timestamps.append((trace_name, event_name))

    incorrect_timestamps = {
        'future_timestamps_in_trace': future_timestamps,
        'past_timestamps_in_trace': past_timestamps
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
    Returns a list of trace names and event names where duplicate events have occurred.
    """
    duplicate_events_in_trace = []

    for trace in log:
        trace_name = trace.get('attributes', {}).get('concept:name', 'Unnamed trace')
        event_set = set()
        duplicate_events = []

        for event in trace.get('events', []):
            event_name = event.get('concept:name', 'Unnamed event')
            # Convert event dictionary to a frozenset of key-value tuples for immutability and comparison
            event_frozenset = frozenset(event.items())
            
            if event_frozenset in event_set:
                duplicate_events.append(event_name)
            else:
                event_set.add(event_frozenset)

        if duplicate_events:
            duplicate_events_in_trace.append({'trace_name': trace_name, 'duplicate_events': duplicate_events})

    return duplicate_events_in_trace

def find_duplicate_traces(log):
    """
    Find and handle duplicate traces.
    Returns a list of trace names where duplicate traces have occurred.
    """
    duplicate_trace_names = set()  # Using a set to avoid duplicate entries
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

def calculate_accuracy_score(results, max_counts):
    # Define weights for each essential assessment
    weights = {
        'timestamp_accuracy': 0.2,
        'duplicate_events': 0.4,
        'duplicate_traces': 0.4
    }
    
    # Extract assessment results
    inaccurate_timestamps = results.get('timestamp_errors', {})
    duplicate_events = results.get('duplicate_events_in_trace', [])
    duplicate_traces = results.get('duplicate_traces', [])

    # Calculate the number of issues in each category
    num_inaccurate_timestamps = len(inaccurate_timestamps['future_timestamps_in_trace']) + len(inaccurate_timestamps['past_timestamps_in_trace'])
    num_duplicate_events = len(duplicate_events)
    num_duplicate_traces = len(duplicate_traces)

    # Calculate timestamp accuracy score
    timestamp_accuracy_score = 1.0 if num_inaccurate_timestamps == 0 else 0.0

    # Normalize the counts to a score between 0 and 1
    scores = {
        'timestamp_accuracy': timestamp_accuracy_score,
        'duplicate_events': max(0, 1 - 10 * num_duplicate_events / max_counts['duplicate_events']),
        'duplicate_traces': max(0, 1 - 10 * num_duplicate_traces / max_counts['duplicate_traces'])
    }

    # Calculate the weighted accuracy score
    accuracy_score = sum(weights[key] * scores[key] for key in weights)
    accuracy_percentage = accuracy_score * 100
    
    # Convert individual scores to percentages
    detailed_scores = {key: round(score * 100, 2) for key, score in scores.items()}
    detailed_scores['overall_accuracy_score'] = round(accuracy_percentage, 2)
    
    return detailed_scores

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

        # Calculate total events and traces for max counts
        total_events = sum(len(trace['events']) for trace in log)
        max_counts = {
            'inaccurate_timestamps': total_events,
            'duplicate_events': total_events,
            'duplicate_traces': len(log)
        }

        results = {
            'status': 'success',
            'timestamp_errors': timestamp_errors,
            'potential_traces_of_a_different_process': outlier_trace_names,
            'duplicate_events_in_trace' : duplicate_events,
            'duplicate_traces' : duplicate_traces
        }

        accuracy_scores = calculate_accuracy_score(results, max_counts)
        results['accuracy_scores'] = accuracy_scores

        return results
    
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