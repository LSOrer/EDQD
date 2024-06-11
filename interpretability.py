from datetime import datetime
from xes_parser import parse_xes 

def check_coarse_timestamps(log):
    """
    Check whether timestamps only capture changes of days, not hours or minutes.
    Returns a message if timestamps only capture changes in days.
    """
    for trace in log:
        for event in trace['events']:
            timestamp = event.get('time:timestamp')
            if timestamp:
                timestamp = datetime.fromisoformat(timestamp)
                if not (timestamp.hour == 0 and timestamp.minute == 0 and timestamp.second == 0 and timestamp.microsecond == 0):
                    return None               
    return "Coarse timestamps"

def assess_interpretability(file_path):
    """
    Assess the interpretability of the XES log.
    Returns a dictionary with the assessment results for interpretability.
    """
    try:
        log = parse_xes(file_path)

        coarse_timestamps = check_coarse_timestamps(log)


        return {
            'status': 'success',
            'coarse_timestamps': coarse_timestamps
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    file_path = 'path_to_your_xes_file.xes'
    results = assess_interpretability(file_path)
    print(results)