from datetime import datetime
import xml.etree.ElementTree as ET

def parse_xes(file_path):
    """
    Parse an XES file and return the log structure.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    log = []
    for trace in root.findall('trace'):
        trace_data = {'attributes': {}, 'events': []}
        for attribute in trace:
            if attribute.tag != 'event':
                trace_data['attributes'][attribute.attrib['key']] = attribute.attrib.get('value', attribute.text)
            else:
                event_data = {}
                for event_attr in attribute:
                    event_data[event_attr.attrib['key']] = event_attr.attrib.get('value', event_attr.text)
                trace_data['events'].append(event_data)
        log.append(trace_data)
    
    return log

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
    #https://xes-standard.org/_media/xes/xesstandarddefinition-2.0.pdf pages 11-12

    transitions = [
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

def check_unrecorded_traces(log, pattern_threshold=3, time_gap_factor=3):
    """
    Check for possible unrecorded traces using pattern analysis and time gap analysis.
    
    Parameters:
    - log: the event log
    - pattern_threshold: threshold for detecting significant deviations in trace length (the lower the more sensitive)
    - time_gap_factor: factor to determine significant time gaps (the lower the more sensitive)
    
    Returns:
    - Two lists: one for pattern anomalies and one for time gap anomalies
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
            trace_name = log[index - 1]['attributes'].get('concept:name', 'Unnamed trace')
            pattern_anomalies.append(trace_name)
    
    time_gap_anomalies = []
    for index in time_gap_indices:
        if index < len(log) - 1:
            trace_name = log[index]['attributes'].get('concept:name', 'Unnamed trace')
            time_gap_anomalies.append(trace_name)
    
    return "Pattern Anomalies:", pattern_anomalies, "Significant Time Gaps:", time_gap_anomalies


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


        return {
            'status': 'success',
            'missing_values': missing_values,
            'incomplete_traces': incomplete_traces,
            'lifecycle_transition': lifecycle_transition_msg,
            'org_resource': org_resource_msg,
            'unrecorded_traces': unrecorded_traces
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