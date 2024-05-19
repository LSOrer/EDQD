import pm4py
from pm4py.objects.log.importer.xes import importer as xes_importer

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
        for attribute in trace.attributes:
            if attribute not in missing_values['trace_attributes']:
                missing_values['trace_attributes'][attribute] = 0
            if trace.attributes[attribute] is None or trace.attributes[attribute] == '':
                missing_values['trace_attributes'][attribute] += 1
    
    # Check for missing values in event attributes
    for trace in log:
        for event in trace:
            for attribute in event:
                if attribute not in missing_values['event_attributes']:
                    missing_values['event_attributes'][attribute] = 0
                if event[attribute] is None or event[attribute] == '':
                    missing_values['event_attributes'][attribute] += 1

    return missing_values

def check_incomplete_traces(log):
    """
    Check for incomplete traces in the XES log based on the 'lifecycle:transition' attribute.
    Returns a list of incomplete trace IDs.
    """
    incomplete_traces = []
    
    for trace in log:
        complete = False
        for event in trace:
            if event.get('lifecycle:transition') == 'complete':
                complete = True
                break
        if not complete:
            incomplete_traces.append(trace.attributes.get('concept:name', 'Unnamed trace'))
    
    return incomplete_traces

def check_attribute_presence(log, attribute_name):
    """
    Check if any event in the log contains the specified attribute.
    Returns True if the attribute is found in any event, otherwise False.
    """
    for trace in log:
        for event in trace:
            if attribute_name in event:
                return True
    return False

def assess_completeness(file_path):
    """
    Assess the completeness of the XES log.
    Returns a dictionary with the assessment results.
    """
    try:
        log = xes_importer.apply(file_path)
        missing_values = check_missing_values(log)
        incomplete_traces = check_incomplete_traces(log)

        # Check for lifecycle:transition and org:resource attributes
        lifecycle_transition_recorded = check_attribute_presence(log, 'lifecycle:transition')
        org_resource_recorded = check_attribute_presence(log, 'org:resource')
        
        # Prepare response messages
        lifecycle_transition_msg = "Transitional information recorded" if lifecycle_transition_recorded else "No transitional information recorded"
        org_resource_msg = "Organizational resource information recorded" if org_resource_recorded else "No organizational resource information recorded"
 
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