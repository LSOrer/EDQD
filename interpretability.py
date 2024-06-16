from datetime import datetime
from xes_parser import parse_xes
from collections import Counter
import statistics
import re

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
    return "Warning coarse timestamps! Only changes in days are recorded"


def check_coarse_org_values(log):
    """
    Check whether the organizational extension of the XES standard records only org:group or org:role.
    If org:resource is present in the event log, return nothing.
    If only org:group is recorded, return "Coarse resource information: only org:group is recorded".
    If only org:role is recorded, return "Coarse resource information: only org:role is recorded".
    """
    org_group_present = False
    org_role_present = False
    org_resource_present = False

    for trace in log:
        for event in trace.get('events', []):
            if 'org:group' in event:
                org_group_present = True
            if 'org:role' in event:
                org_role_present = True
            if 'org:resource' in event:
                org_resource_present = True

    if org_resource_present:
        return None
    elif org_group_present and not org_role_present:
        return "Coarse resource information: only org:group is recorded"
    elif org_role_present and not org_group_present:
        return "Coarse resource information: only org:role is recorded"
    elif org_group_present and org_role_present:
        return "Coarse resource information: both org:group and org:role are recorded, but org:resource is missing"

    return None

def assess_activity_name_granularity(log):
    """
    Assess the granularity of activity names in the event log.
    Returns a report indicating potential issues with coarse activity names.
    """
    activity_names = []

    for trace in log:
        for event in trace.get('events', []):
            activity_name = event.get('concept:name')
            if activity_name:
                activity_names.append(activity_name)

    if not activity_names:
        return "No activity names found in the log."

    # Length and complexity analysis
    lengths = [len(name) for name in activity_names]
    avg_length = statistics.mean(lengths)

    # Frequency analysis
    frequency = Counter(activity_names)
    most_common = frequency.most_common(1)[0] if frequency else None

    # Semantic analysis (basic example using regex to find descriptive words)
    descriptive_words = [len(re.findall(r'\w+', name)) for name in activity_names]
    avg_descriptive_words = statistics.mean(descriptive_words)
    
    # We assume that the activity name granularity is coarse if the number of words is < 2 and the average length is < 6
    activity_names_too_coarse = avg_descriptive_words < 2 or avg_length < 6

    activity_name_report = {
        "average_length": avg_length,
        "most_common_activity": most_common,
        "average_descriptive_words": avg_descriptive_words,
        "activity_names_too_coarse": activity_names_too_coarse
    }

    return activity_name_report

def assess_interpretability(file_path):
    """
    Assess the interpretability of the XES log.
    Returns a dictionary with the assessment results for interpretability.
    """
    try:
        log = parse_xes(file_path)

        coarse_timestamps = check_coarse_timestamps(log)
        org_information = check_coarse_org_values(log)
        coarse_activity_name = assess_activity_name_granularity(log)


        return {
            'status': 'success',
            'coarse_timestamps' : coarse_timestamps,
            'coarse_resource_information' : org_information,
            'coarse_activity_names' : coarse_activity_name
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