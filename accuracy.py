from datetime import datetime
from xes_parser import parse_xes 

def check_timestamp_accuracy(log):
    """
    Check if timestamps are within a reasonable range (i.e., no future dates, no dates before 1900-01-01).
    """
    future_timestamps = []
    past_timestamps = []
    now = datetime.now().replace(tzinfo=None) # ensure that all datetime objects have the same timezone awareness
    min_date = datetime(1900, 1, 1)

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

def assess_accuracy(file_path):
    """
    Assess the accuracy of the XES log.
    Returns a dictionary with the assessment results for accuracy.
    """
    try:
        log = parse_xes(file_path)

        timestamp_errors = check_timestamp_accuracy(log)


        return {
            'status': 'success',
            'timestamp_errors': timestamp_errors,
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