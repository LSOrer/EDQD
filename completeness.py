from datetime import datetime
from xes_parser import parse_xes 
import xml.etree.ElementTree as ET

def check_missing_values(log):
    """
    Check for missing values in the XES log.
    Returns a dictionary with the counts of missing values for each attribute.
    """
    missing_values = {
        'trace_attributes': {},
        'event_attributes': {}
    }

    # Check for missing values in trace attributes
    for trace in log:
        for attribute, value in trace['attributes'].items():
            if attribute not in missing_values['trace_attributes']:
                missing_values['trace_attributes'][attribute] = 0
            if value is None or value == '':
                missing_values['trace_attributes'][attribute] += 1
    
    # Check for missing values in event attributes
    for trace in log:
        for event in trace['events']:
            for attribute, value in event.items():
                if attribute not in missing_values['event_attributes']:
                    missing_values['event_attributes'][attribute] = 0
                if value is None or value == '':
                    missing_values['event_attributes'][attribute] += 1

    return missing_values

def check_incomplete_traces(log):
    """
    Check for incomplete traces in the XES log based on the 'lifecycle:transition' attribute.
    Returns a list of incomplete trace IDs.
    """
    # Transition states that end a trace according to the XES standard 
    # https://xes-standard.org/_media/xes/xesstandarddefinition-2.0.pdf pages 11-12

    transitions = [
    'COMPLETE',
    'complete', 
    'autoskip', 
    'manualskip', 
    'withdraw', 
    'ate_abort', 
    'pi_abort'
    ]

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

def check_unrecorded_traces(log, pattern_threshold=1, time_gap_factor=3):
    """
    Check for possible unrecorded traces using pattern analysis and time gap analysis.
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

    def analyze_time_gaps(log, factor):
        significant_gaps = []
        for i, trace in enumerate(log):
            timestamps = [datetime.fromisoformat(event['time:timestamp']) for event in trace['events'] if 'time:timestamp' in event]
            if len(timestamps) > 1:
                gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)]
                mean_gap = sum(gaps) / len(gaps)
                for j, gap in enumerate(gaps):
                    if gap > factor * mean_gap:
                        significant_gaps.append(i)
        return significant_gaps

    # Perform pattern analysis
    pattern_missing_indices = analyze_trace_patterns(log, pattern_threshold)

    # Perform time gap analysis
    time_gap_indices = analyze_time_gaps(log, time_gap_factor)

    # Identify trace names for the results
    pattern_anomalies = []
    for index in pattern_missing_indices:
        if index > 0:
            trace_name = log[index]['attributes'].get('concept:name', 'Unnamed trace')
            pattern_anomalies.append(trace_name)
    
    time_gap_anomalies = []
    for index in time_gap_indices:
        if index < len(log) - 1:
            trace_name = log[index]['attributes'].get('concept:name', 'Unnamed trace')
            time_gap_anomalies.append(trace_name)
    
    potential_unrecorded_traces = {
        "Trace Pattern Anomalies": pattern_anomalies,
        "Significant Time Gaps": time_gap_anomalies
    }

    return potential_unrecorded_traces

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
    Returns a list of trace names where the event ordering is incorrect.
    """
    disordered_traces = []

    for trace in log:
        trace_name = trace['attributes'].get('concept:name', 'Unnamed trace')
        timestamps = []

        for event in trace['events']:
            timestamp_str = event.get('time:timestamp')
            if timestamp_str:
                timestamp = datetime.fromisoformat(timestamp_str)
                timestamps.append(timestamp)

        # Check if the list of timestamps is sorted
        if timestamps != sorted(timestamps):
            disordered_traces.append(trace_name)

    return disordered_traces

def assess_completeness(file_path):
    """
    Assess the completeness of the XES log.
    Returns a dictionary with the assessment results.
    """
    try:
        log = parse_xes(file_path)
        missing_values = check_missing_values(log)
        incomplete_traces = check_incomplete_traces(log)

        # Check for lifecycle:transition and org:resource attributes
        lifecycle_transition_recorded = check_attribute_presence(log, 'lifecycle:transition')
        org_resource_recorded = check_attribute_presence(log, 'org:resource')
        
        # Prepare response messages
        lifecycle_transition_msg = "lifecycle:transition attribute present" if lifecycle_transition_recorded else "no lifecycle:transition information"
        org_resource_msg = "org:resource attribute present" if org_resource_recorded else "no org:resource information"
 
        unrecorded_traces = check_unrecorded_traces(log)

        orphan_events = find_orphan_events(file_path)

        disordered_traces = find_disordered_traces(log)

        return {
            'status': 'success',
            'missing_values': missing_values,
            'incomplete_traces': incomplete_traces,
            'lifecycle_transition': lifecycle_transition_msg,
            'org_resource': org_resource_msg,
            'unrecorded_traces': unrecorded_traces,
            'orphan_events': orphan_events,
            'disordered_traces': disordered_traces
        }
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    file_path = '/Users/babettebaier/Desktop/EDQD/2easy2missing.xes'
    results = assess_completeness(file_path)
    print(results)