from datetime import datetime
from xes_parser import parse_xes
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
    total_length = 0
    total_words = 0
    most_common_name = None
    most_common_count = 0
    name_counts = {}

    for trace in log:
        for event in trace.get('events', []):
            activity_name = event.get('concept:name')
            if activity_name:
                activity_names.append(activity_name)
                length = len(activity_name)
                total_length += length

                word_count = len(re.findall(r'\w+', activity_name))
                total_words += word_count

                # Track the most common activity name
                if activity_name in name_counts:
                    name_counts[activity_name] += 1
                else:
                    name_counts[activity_name] = 1

                if name_counts[activity_name] > most_common_count:
                    most_common_count = name_counts[activity_name]
                    most_common_name = activity_name

    if not activity_names:
        return "No activity names found in the log."

    avg_length = total_length / len(activity_names)
    avg_descriptive_words = total_words / len(activity_names)

    # We assume that the activity name granularity is coarse if the number of words is < 2 and the average length is < 6
    activity_names_too_coarse = avg_descriptive_words < 2 or avg_length < 6

    activity_name_report = {
        "average_length": avg_length,
        "most_common_activity": (most_common_name, most_common_count),
        "average_descriptive_words": avg_descriptive_words,
        "activity_names_too_coarse": activity_names_too_coarse
    }

    return activity_name_report

def calculate_interpretability_score(results):
    """
    Calculate the interpretability score based on assessment results.
    """
    # Define weights for each assessment
    weights = {
        'timestamp_coarseness': 0.3,
        'resource_information': 0.3,
        'activity_name_granularity': 0.4
    }

    # Extract assessment results
    coarse_timestamps = results.get('coarse_timestamps')
    org_information = results.get('coarse_resource_information')
    coarse_activity_name = results.get('coarse_activity_names', {})

    # Calculate individual scores
    timestamp_coarseness_score = 100 if coarse_timestamps is None else 0

    if org_information is None:
        resource_information_score = 100
    elif org_information == "Coarse resource information: only org:group is recorded" or org_information == "Coarse resource information: only org:role is recorded":
        resource_information_score = 50
    elif org_information == "Coarse resource information: both org:group and org:role are recorded, but org:resource is missing":
        resource_information_score = 80
    else:
        resource_information_score = 0

    activity_name_granularity_score = 100 if not coarse_activity_name.get('activity_names_too_coarse') else 0

    # Calculate the weighted interpretability score
    interpretability_score = (
        weights['timestamp_coarseness'] * timestamp_coarseness_score +
        weights['resource_information'] * resource_information_score +
        weights['activity_name_granularity'] * activity_name_granularity_score
    ) / 100

    interpretability_percentage = interpretability_score * 100

    # Convert individual scores to percentages
    detailed_scores = {
        'timestamp_coarseness': timestamp_coarseness_score,
        'resource_information': resource_information_score,
        'activity_name_granularity': activity_name_granularity_score,
        'overall_interpretability_score': interpretability_percentage
    }

    return detailed_scores

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

        results = {
            'status': 'success',
            'coarse_timestamps': coarse_timestamps,
            'coarse_resource_information': org_information,
            'coarse_activity_names': coarse_activity_name
        }

        interpretability_scores = calculate_interpretability_score(results)
        results['interpretability_scores'] = interpretability_scores

        return results
    
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