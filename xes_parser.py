import xml.etree.ElementTree as ET
import re

def remove_namespace(file_path):
    """
    Remove the xmlns attribute from the root tag in the XES file.
    """
    with open(file_path, 'r') as file:
        content = file.read()
    
    # Remove the xmlns attribute
    content = re.sub(r'xmlns="[^"]+"', '', content)
    
    with open(file_path, 'w') as file:
        file.write(content)

def parse_xes(file_path):
    """
    Parse an XES file and return the log structure.
    """

    # Remove the namespace to avoid parsing issues
    remove_namespace(file_path)

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