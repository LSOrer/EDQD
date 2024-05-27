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
    #https://xes-standard.org/_media/xes/xesstandarddefinition-2.0.pdf page 12

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
 
        return {
            'status': 'success',
            'missing_values': missing_values,
            'incomplete_traces': incomplete_traces,
            'lifecycle_transition': lifecycle_transition_msg,
            'org_resource': org_resource_msg
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