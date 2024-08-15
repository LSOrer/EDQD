import re
from xes_parser import parse_xes

def it_system_noise(event):
    activity_name = event.get('concept:name', '').lower()
    noise_keywords = {"system start", "system shutdown", "maintenance", "debug", "log", "error", "warning", "info"}
    return any(re.search(r'\b' + re.escape(keyword) + r'\b', activity_name) for keyword in noise_keywords)

def check_noise_events(log, noise_criteria):
    """
    Detect events that are considered noise or extraneous to the main process.
    Returns a dictionary with trace names as keys and lists of noise events as values.
    """
    noise_events = {}

    for trace in log:
        trace_name = trace.get('attributes', {}).get('concept:name', 'Unnamed trace')
        trace_noise_events = []

        for event in trace.get('events', []):
            if noise_criteria(event):
                trace_noise_events.append(event)

        if trace_noise_events:
            noise_events[trace_name] = trace_noise_events

    return noise_events

def calculate_relevancy_score(results, total_events):
    """
    Calculate the relevancy score based on the number of noise events.
    """
    noise_events = results.get('noise_events', {})
    num_noise_events = sum(len(events) for events in noise_events.values())

    # Calculate the relevancy score
    relevancy_score = max(0, (1 - 10 * num_noise_events / total_events) * 100)
    
    return relevancy_score

def assess_relevancy(file_path):
    """
    Assess the relevancy of the XES log.
    Returns a dictionary with the assessment results for relevancy.
    """
    try:
        log = parse_xes(file_path)

        noise_events = check_noise_events(log, it_system_noise)

        total_events = sum(len(trace.get('events', [])) for trace in log)
        relevancy_score = round(calculate_relevancy_score({'noise_events': noise_events}, total_events), 2)

        return {
            'status': 'success',
            'noise_events': noise_events,
            'overall_relevancy_score': relevancy_score
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    file_path = 'path_to_your_xes_file.xes'
    results = assess_relevancy(file_path)
    print(results)