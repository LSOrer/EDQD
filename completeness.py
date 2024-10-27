from datetime import datetime
from xes_parser import parse_xes 
from lxml import etree as ET

def is_missing_value(value):
    """
    Check if the value is considered as missing.
    """
    missing_strings = {'', 'null', 'Null', 'NULL', 'na', 'NA', 'N/A', 'n/a', 'nan' , 'NaN', 'none', 'None', 'NONE'}
    if value is None:
        return True
    if isinstance(value, str): 
        if value.strip() in missing_strings: # delete whitespaces
            return True
    return False

def check_missing_attribute_values(log):
    """
    Check for missing attribute values in the XES log.
    Returns a dictionary with the counts of missing values for each attribute.
    """
    missing_attribute_values = {
        'trace_attributes': {},
        'event_attributes': {}
    }

    # Check for missing values in trace attributes
    for trace in log:
        for attribute, value in trace['attributes'].items():
            if attribute not in missing_attribute_values['trace_attributes']:
                missing_attribute_values['trace_attributes'][attribute] = 0
            if is_missing_value(value):
                missing_attribute_values['trace_attributes'][attribute] += 1
    
    # Check for missing values in event attributes
    for trace in log:
        for event in trace['events']:
            for attribute, value in event.items():
                if attribute not in missing_attribute_values['event_attributes']:
                    missing_attribute_values['event_attributes'][attribute] = 0
                if is_missing_value(value):
                    missing_attribute_values['event_attributes'][attribute] += 1

    return missing_attribute_values

def check_incomplete_traces(log):
    """
    Check for incomplete traces in the XES log based on the 'lifecycle:transition' attribute.
    Returns a list of incomplete trace IDs.
    """
    # Transition states that end a trace according to the XES standard 
    # https://pure.tue.nl/ws/portalfiles/portal/3981980/692728941269079.pdf pages 11-12

    transitions = {'COMPLETE', 'complete', 'autoskip', 'manualskip', 'withdraw', 'ate_abort', 'pi_abort', 'Closed'}
    incomplete_traces = []
    
    if check_attribute_presence(log, 'lifecycle:transition'):
        for trace in log:
            complete = False
            for event in trace['events']:
                if event.get('lifecycle:transition') in transitions:
                    complete = True
                    break
            if not complete:
                incomplete_traces.append(trace['attributes'].get('concept:name', 'Unnamed trace'))
        
    return incomplete_traces

def check_attribute_presence(log, attribute_name):
    """
    Check if any event in the log contains the specified attribute.
    Returns True if the attribute is found in any event, otherwise False.
    """
    for trace in log:
        for event in trace['events']:
            if attribute_name in event:
                return True
    return False

def check_unrecorded_traces(log, pattern_threshold, time_gap_factor_traces):
    """
    Check for possible unrecorded traces using pattern analysis and inter trace time gap analysis.
    pattern_threshold: threshold for detecting significant deviations in trace length (the lower the more sensitive)
    time_gap_factor: factor to determine significant time gaps (the lower the more sensitive)
    Returns a dictionary with pattern anomalies and time gap anomalies
    """
    
    def analyze_trace_patterns(log, threshold):
        trace_lengths = [len(trace['events']) for trace in log]
        mean_length = sum(trace_lengths) / len(trace_lengths)
        # Check for significant deviations
        deviations = [abs(length - mean_length) for length in trace_lengths]
        potential_missing_indices = [i for i, dev in enumerate(deviations) if dev > threshold * mean_length]
        return potential_missing_indices

    def analyze_inter_trace_gaps(log, factor):
        trace_times = []
        
        # Extract the opening and closing time of each trace
        for trace in log:
            events = [datetime.fromisoformat(event['time:timestamp']) for event in trace['events'] if 'time:timestamp' in event]
            if events:
                opening_time = events[0]
                closing_time = events[-1]
                trace_times.append((opening_time, closing_time))
        
        # Sort traces by opening time
        trace_times.sort(key=lambda x: x[0])
        
        inter_trace_gaps = []
        trace_pairs = []
        for i in range(1, len(trace_times)):
            previous_closing_time = trace_times[i-1][1]
            current_opening_time = trace_times[i][0]
            
            # Only consider non-overlapping traces
            if current_opening_time > previous_closing_time:
                gap = (current_opening_time - previous_closing_time).total_seconds()
                inter_trace_gaps.append(gap)
                trace_pairs.append((i-1, i))
        
        mean_gap = sum(inter_trace_gaps) / len(inter_trace_gaps) if inter_trace_gaps else 0
        
        significant_gaps = []
        for i, gap in enumerate(inter_trace_gaps):
            if gap > factor * mean_gap:
                trace1_index, trace2_index = trace_pairs[i]
                trace1_name = log[trace1_index]['attributes'].get('concept:name', 'Unnamed trace')
                trace2_name = log[trace2_index]['attributes'].get('concept:name', 'Unnamed trace')
                significant_gaps.append({
                    'Large Gap between': f"{trace1_name} and {trace2_name}",
                    'gap': gap
                })
        
        return significant_gaps

    # Perform pattern analysis
    pattern_missing_indices = analyze_trace_patterns(log, pattern_threshold)

    # Perform inter trace time gap analysis
    trace_time_gap_anomalies = analyze_inter_trace_gaps(log, time_gap_factor_traces)

    # Identify trace names and the number of events in the traces for the results
    pattern_anomalies = []
    for index in pattern_missing_indices:
        if index > 0:
            trace_name = log[index]['attributes'].get('concept:name', 'Unnamed trace')
            num_events = len(log[index]['events'])
            pattern_anomalies.append({
                'trace_name': trace_name,
                'num_events': num_events
            })
    
    potential_unrecorded_traces = {
        "trace_pattern_anomalies": pattern_anomalies,
        "unusual_inter_trace_time_gaps": trace_time_gap_anomalies
    }

    return potential_unrecorded_traces


def check_unrecorded_events(log, time_gap_factor_events):
    """
    Check for possible unrecorded events using time gap analysis.
    time_gap_factor: factor to determine significant time gaps (the lower the more sensitive)
    Returns a list of trace names and the events with large gaps between them.
    """
    def analyze_event_time_gaps(trace, factor):
        significant_gaps = []
        timestamps = [datetime.fromisoformat(event['time:timestamp']) for event in trace['events'] if 'time:timestamp' in event]
        events = [event['concept:name'] for event in trace['events'] if 'time:timestamp' in event]
        
        if len(timestamps) > 1:
            gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)]
            mean_gap = sum(gaps) / len(gaps)
            for i, gap in enumerate(gaps):
                if gap > factor * mean_gap:
                    significant_gaps.append({
                        'event1': events[i],
                        'event2': events[i+1],
                        'gap': gap
                    })
        return significant_gaps
    
    event_time_gap_anomalies = []
    
    # Analyze each trace
    for trace in log:
        trace_name = trace['attributes'].get('concept:name', 'Unnamed trace')
        significant_gaps = analyze_event_time_gaps(trace, time_gap_factor_events)
        
        if significant_gaps:
            for gap_info in significant_gaps:
                event_time_gap_anomalies.append({
                    'trace_name': trace_name,
                    'message': f"Large gap between {gap_info['event1']} and {gap_info['event2']}, gap: {gap_info['gap']} seconds"
                })
    
    return event_time_gap_anomalies
    

def find_orphan_events(file_path):
    """
    Find events that are not associated to a trace in an XES file.
    Returns a list of the attributes of orphan events found in the XES file.
    """
    root = ET.parse(file_path)
    
    # Find all traces
    traces = root.findall('trace')
    
    # Find all events associated with traces
    associated_events = []
    for trace in traces:
        events = trace.findall('event')
        associated_events.extend(events)
    
    # Find all events in the log
    all_events = root.findall('event')
    
    # Unassociated events are those in all_events but not in associated_events
    unassociated_events = [event for event in all_events if event not in associated_events]
    
    # Collect attributes of the unassociated events
    orphan_events = []
    for event in unassociated_events:
        attributes = {}
        for child in event:
            attributes[child.attrib['key']] = child.attrib['value']
        orphan_events.append(attributes)
    
    return orphan_events

def find_disordered_traces(log):
    """
    Check if the events of each trace in the event log are ordered by their timestamps.
    Returns a list of dictionaries with trace names and the specific disordered event names.
    """
    disordered_traces = []

    for trace in log:
        trace_name = trace['attributes'].get('concept:name', 'Unnamed trace')
        timestamps = []

        for event in trace['events']:
            timestamp_str = event.get('time:timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
                timestamps.append((timestamp, event['concept:name']))  # Store timestamp and event name

        # Check if the list of timestamps is sorted
        sorted_timestamps = sorted(timestamps, key=lambda x: x[0])

        # Identify disordered events by comparing original order with sorted order
        disordered_events = [
            event_name for (original, event_name), (sorted_, _) in zip(timestamps, sorted_timestamps) if original != sorted_
        ]

        if disordered_events:
            disordered_traces.append({
                'trace_name': trace_name,
                'disordered_events': disordered_events
            })

    return disordered_traces

def calculate_completeness_score(results, max_counts):
    # Define weights for each essential assessment
    weights = {
        'C7_Disordered_Traces': 0.25,
        'C2_Incomplete_Traces': 0.25,
        'C1_Missing_Values': 0.25,
        'C6_Orphan_Events': 0.25
    }
    
    # Extract assessment results
    disordered_traces = results.get('C7_Disordered_Traces', [])
    incomplete_traces = results.get('C2_Incomplete_Traces', [])
    missing_attribute_values = results.get('C1_Missing_Values', {})
    orphan_events = results.get('C6_Orphan_Events', [])

    # Calculate the number of issues in each category
    num_disordered_traces = len(disordered_traces)
    num_incomplete_traces = len(incomplete_traces)
    num_missing_values = sum(missing_attribute_values['trace_attributes'].values()) + sum(missing_attribute_values['event_attributes'].values())
    num_orphan_events = len(orphan_events)

    # Normalize the counts to a score between 0 and 1
    scores = {
        'C7_Disordered_Traces': max(0, 1 - 10 * num_disordered_traces / max_counts['C7_Disordered_Traces']),
        'C2_Incomplete_Traces': max(0, 1 - 10 * num_incomplete_traces / max_counts['C2_Incomplete_Traces']),
        'C1_Missing_Values': max(0, 1 - 10 * num_missing_values / max_counts['C1_Missing_Values']),
        'C6_Orphan_Events': max(0, 1 - 10 * num_orphan_events / max_counts['C6_Orphan_Events'])
    }

    # Calculate the weighted completeness score
    completeness_score = sum(weights[key] * scores[key] for key in weights)
    completeness_percentage = completeness_score * 100
    
    # Convert individual scores to percentages
    detailed_scores = {key: round(score * 100, 2) for key, score in scores.items()}
    detailed_scores['C0_Overall_Completeness_Score'] = round(completeness_percentage, 2)
    
    return detailed_scores

def assess_completeness(file_path, thresholds):
    """
    Assess the completeness of the XES log.
    Returns a dictionary with the assessment results.
    """
    try:
        log = parse_xes(file_path)

        # Extract dynamic threshold values
        pattern_threshold = thresholds.get('pattern_threshold', 1)
        time_gap_factor_traces = thresholds.get('time_gap_factor_traces', 2)
        time_gap_factor_events = thresholds.get('time_gap_factor_events', 3)

        missing_attribute_values = check_missing_attribute_values(log)
        incomplete_traces = check_incomplete_traces(log)
        unrecorded_traces = check_unrecorded_traces(log, pattern_threshold, time_gap_factor_traces)
        orphan_events = find_orphan_events(file_path)
        disordered_traces = find_disordered_traces(log)
        missing_events = check_unrecorded_events(log, time_gap_factor_events)


        # Check for lifecycle:transition and org:resource attributes
        lifecycle_transition_recorded = check_attribute_presence(log, 'lifecycle:transition')
        org_resource_recorded = check_attribute_presence(log, 'org:resource')
        
        # Prepare response messages
        lifecycle_transition_msg = "lifecycle:transition attribute present" if lifecycle_transition_recorded else "no lifecycle:transition information"
        org_resource_msg = "org:resource attribute present" if org_resource_recorded else "no org:resource information"

        # Calculate total attributes and events for max counts
        total_attributes = 0
        total_events = 0
        for trace in log:
            total_attributes += len(trace['attributes'])
            total_events += len(trace['events'])
            for event in trace['events']:
                total_attributes += len(event)
        
        max_counts = {
            'C7_Disordered_Traces': len(log),
            'C2_Incomplete_Traces': len(log),
            'C1_Missing_Values': total_attributes,
            'C6_Orphan_Events': total_events
        }

        results = {
            'z_status': 'success',
            'C1_Missing_Values': missing_attribute_values,
            'C2_Incomplete_Traces': incomplete_traces,
            'C3_Attribute_Presence': {'lifecycle_transition': lifecycle_transition_msg,'org_resource': org_resource_msg},
            'C4_Unrecorded_Traces': unrecorded_traces,
            'C6_Orphan_Events': orphan_events,
            'C7_Disordered_Traces': disordered_traces,
            'C5_Unrecorded_Events': missing_events
        }

        completeness_scores = calculate_completeness_score(results, max_counts)
        results['C0_Completeness_Scores'] = completeness_scores

        return results
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    file_path = 'path_to_your_xes_file.xes' # Replace with your actual file path
    results = assess_completeness(file_path)
    print(results)