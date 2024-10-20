import re
import xml.etree.ElementTree as ET
from xes_parser import parse_xes
from datetime import datetime

def validate_attribute_keys(log):
    """
    Validate that attribute keys contain no line feeds, no carriage returns, and no tabs. (XES Standard Version 2.0 - Section 2.2 Attributes)
    Returns a dictionary with trace names as keys and lists of events with invalid attribute keys as values.
    """
    invalid_attribute_keys = {}
    invalid_characters_pattern = re.compile(r'[\n\r\t]|\\n|\\r|\\t|    ')

    for trace in log:
        trace_name = trace.get('attributes', {}).get('concept:name', 'Unnamed trace')
        trace_invalid_keys = []

        # Check attribute keys in trace attributes
        for key in trace.get('attributes', {}).keys():
            if invalid_characters_pattern.search(key):
                trace_invalid_keys.append(key)

        # Check attribute keys in event attributes
        for event in trace.get('events', []):
            for key in event.keys():
                if invalid_characters_pattern.search(key):
                    trace_invalid_keys.append(key)

        if trace_invalid_keys:
            if trace_name not in invalid_attribute_keys:
                invalid_attribute_keys[trace_name] = []
            invalid_attribute_keys[trace_name].extend(trace_invalid_keys)

    return invalid_attribute_keys

def validate_unique_keys(file_path):
    """
    Validate that keys are unique within their enclosing container (except within lists). (XES Standard Version 2.0 - Section 2.2 Attributes)
    Returns a dictionary with trace names as keys and lists of containers with duplicate keys as values.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    duplicate_keys = {}

    for trace in root.findall('trace'):
        trace_name = 'Unnamed trace'
        for attr in trace.findall('string'):
            if attr.attrib.get('key') == 'concept:name':
                trace_name = attr.attrib.get('value', 'Unnamed trace')
                break
        
        trace_keys = set()
        trace_duplicate_keys = set()
        event_duplicate_keys = set()

        # Check attribute keys in trace attributes
        for attribute in trace:
            if attribute.tag != 'event':
                key = attribute.attrib['key']
                if key in trace_keys:
                    trace_duplicate_keys.add(key)
                else:
                    trace_keys.add(key)

        # Check attribute keys in event attributes
        for event in trace.findall('event'):
            event_keys = set()
            for event_attr in event:
                key = event_attr.attrib['key']
                if key in event_keys:
                    event_duplicate_keys.add(key)
                else:
                    event_keys.add(key)

        if trace_duplicate_keys or event_duplicate_keys:
            duplicate_keys[trace_name] = {
                'trace_duplicate_keys': list(trace_duplicate_keys),
                'event_duplicate_keys': list(event_duplicate_keys)
            }

    return duplicate_keys

def validate_attribute_values(file_path):
    """
    Validate that the values of attributes conform to their specified data types.
    Returns a dictionary with trace names as keys and lists of attributes with invalid data types as values.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    invalid_data_types = {}

    def is_valid_int(value):
        try:
            int(value)
            return True
        except ValueError:
            return False

    def is_valid_float(value):
        try:
            float(value)
            return True
        except ValueError:
            return False

    def is_valid_date(value):
        try:
            datetime.fromisoformat(value)
            return True
        except ValueError:
            return False

    def is_valid_boolean(value):
        return value.lower() in ['true', 'false']

    for trace in root.findall('trace'):
        trace_name = 'Unnamed trace'
        for attr in trace.findall('string'):
            if attr.attrib.get('key') == 'concept:name':
                trace_name = attr.attrib.get('value', 'Unnamed trace')
                break
        
        invalid_attributes = []

        def validate_attribute(attribute):
            key = attribute.attrib['key']
            value = attribute.attrib.get('value', attribute.text)
            tag = attribute.tag

            if tag == 'int' and not is_valid_int(value):
                invalid_attributes.append({'key': key, 'value': value, 'expected_type': 'int'})
            elif tag == 'float' and not is_valid_float(value):
                invalid_attributes.append({'key': key, 'value': value, 'expected_type': 'float'})
            elif tag == 'date' and not is_valid_date(value):
                invalid_attributes.append({'key': key, 'value': value, 'expected_type': 'date'})
            elif tag == 'boolean' and not is_valid_boolean(value):
                invalid_attributes.append({'key': key, 'value': value, 'expected_type': 'boolean'})

        # Check attribute values in trace attributes
        for attribute in trace:
            if attribute.tag != 'event':
                validate_attribute(attribute)

        # Check attribute values in event attributes
        for event in trace.findall('event'):
            for event_attr in event:
                validate_attribute(event_attr)

        if invalid_attributes:
            invalid_data_types[trace_name] = invalid_attributes

    return invalid_data_types

def check_allowed_data_types(file_path):
    """
    Check every data type in the event log against a list of allowed data types.
    Returns a dictionary for each unsupported data type found, including trace name, attribute name, and unsupported data type.
    """
    allowed_data_types = {'string', 'date', 'int', 'float', 'boolean', 'id', 'list', 'container', 'event'}
    
    tree = ET.parse(file_path)
    root = tree.getroot()

    unsupported_data_types = []

    for trace in root.findall('trace'):
        trace_name = trace.find('string[@key="concept:name"]').attrib.get('value', 'Unnamed trace')

        # Check attribute data types in trace attributes
        for attribute in trace:
            if attribute.tag not in allowed_data_types:
                unsupported_data_types.append({
                    "trace_name": trace_name,
                    "trace_attribute_name": attribute.attrib.get('key', 'Unnamed attribute'),
                    "unsupported_data_type": attribute.tag
                })

        # Check attribute data types in event attributes
        for event in trace.findall('event'):
            event_name = event.find('string[@key="concept:name"]').attrib.get('value', 'Unnamed event')
            for event_attr in event:
                if event_attr.tag not in allowed_data_types:
                    unsupported_data_types.append({
                        "trace_name": trace_name,
                        "event_name": event_name,
                        "event_attribute_name": event_attr.attrib.get('key', 'Unnamed attribute'),
                        "unsupported_data_type": event_attr.tag
                    })

    if unsupported_data_types:
        return unsupported_data_types
    else:
        return ["All data types are supported according to the XES standard"]

def derive_timestamp_pattern(timestamp):
    """
    Derive a regex pattern and format level from a given timestamp.
    """
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}", timestamp):
        return r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}", 4
    elif re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}", timestamp):
        return r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}", 3
    elif re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", timestamp):
        return r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", 2
    elif re.match(r"\d{4}-\d{2}-\d{2}", timestamp):
        return r"\d{4}-\d{2}-\d{2}", 1
    else:
        return None, 0

def get_timestamp_format_level(timestamp):
    """
    Determine the format level of the timestamp.
    """
    if re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}", timestamp):
        return 4
    elif re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}", timestamp):
        return 3
    elif re.match(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}", timestamp):
        return 2
    elif re.match(r"\d{4}-\d{2}-\d{2}", timestamp):
        return 1
    else:
        return 0

def validate_timestamp_consistency(file_path):
    """
    Validate the validity and consistency of timestamps in the event log.
    Returns a list of trace names if invalid or inconsistent timestamp formats are found.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    first_timestamp = None
    inconsistent_trace_names = set()

    for trace in root.findall('trace'):
        trace_name = 'Unnamed trace'
        for attr in trace.findall('string'):
            if attr.attrib.get('key') == 'concept:name':
                trace_name = attr.attrib.get('value', 'Unnamed trace')
                break

        for event in trace.findall('event'):
            for event_attr in event:
                if event_attr.tag == 'date':
                    value = event_attr.attrib.get('value', event_attr.text)
                    if first_timestamp is None:
                        first_timestamp = value
                        pattern_str, format_level = derive_timestamp_pattern(first_timestamp)
                        if pattern_str is None:
                            inconsistent_trace_names.add(trace_name)
                            break
                        pattern = re.compile(pattern_str)
                    else:
                        current_format_level = get_timestamp_format_level(value)
                        if current_format_level != format_level or not pattern.match(value):
                            inconsistent_trace_names.add(trace_name)
                            break

    if first_timestamp is None:
        return ["No timestamps found in the event log."]
    
    if not inconsistent_trace_names:
        return ["The syntax of all timestamps is consistent."]
    
    return list(inconsistent_trace_names)

def validate_timestamp_logical_constraints(file_path):
    """
    Validate the logical constraints of timestamps in the event log.
    Returns a list of messages if invalid logical constraints are found in timestamps.
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    # Patterns for different levels of timestamp details
    patterns = [
        (re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}[+-]\d{2}:\d{2}"), 4),  # Full timestamp with timezone
        (re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}"), 3),  # Timestamp with milliseconds
        (re.compile(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}"), 2),  # Timestamp with seconds
        (re.compile(r"\d{4}-\d{2}-\d{2}"), 1)  # Date only
    ]
    
    issues = []

    def is_valid_date(year, month, day):
        """Check if the given year, month, day constitute a valid date."""
        try:
            datetime(year, month, day)
            return True
        except ValueError:
            return False

    def is_valid_time(hour, minute, second, millisecond=0):
        """Check if the given hour, minute, second, and optional millisecond constitute a valid time."""
        if hour < 0 or hour >= 24:
            return False
        if minute < 0 or minute >= 60:
            return False
        if second < 0 or second >= 60:
            return False
        if millisecond < 0 or millisecond >= 1000:
            return False
        return True

    for trace in root.findall('trace'):
        trace_name = trace.find('string[@key="concept:name"]').attrib.get('value', 'Unnamed trace')
        for event in trace.findall('event'):
            event_name = event.find('string[@key="concept:name"]').attrib.get('value', 'Unnamed event')
            for event_attr in event:
                if event_attr.tag == 'date':
                    value = event_attr.attrib.get('value', event_attr.text)
                    valid = False
                    for pattern, level in patterns:
                        if pattern.match(value):
                            match = pattern.match(value)
                            if level == 1:  # YYYY-MM-DD
                                year, month, day = int(match.group(0)[:4]), int(match.group(0)[5:7]), int(match.group(0)[8:10])
                                if not is_valid_date(year, month, day):
                                    issues.append(f"Trace: {trace_name}, Event: {event_name}, Invalid date: {value}")
                            elif level == 2:  # YYYY-MM-DDThh:mm:ss
                                year, month, day = int(match.group(0)[:4]), int(match.group(0)[5:7]), int(match.group(0)[8:10])
                                hour, minute, second = int(match.group(0)[11:13]), int(match.group(0)[14:16]), int(match.group(0)[17:19])
                                if not is_valid_date(year, month, day) or not is_valid_time(hour, minute, second):
                                    issues.append(f"Trace: {trace_name}, Event: {event_name}, Invalid date/time: {value}")
                            elif level == 3:  # YYYY-MM-DDThh:mm:ss.sss
                                year, month, day = int(match.group(0)[:4]), int(match.group(0)[5:7]), int(match.group(0)[8:10])
                                hour, minute, second = int(match.group(0)[11:13]), int(match.group(0)[14:16]), int(match.group(0)[17:19])
                                millisecond = int(match.group(0)[20:23])
                                if not is_valid_date(year, month, day) or not is_valid_time(hour, minute, second, millisecond):
                                    issues.append(f"Trace: {trace_name}, Event: {event_name}, Invalid date/time: {value}")
                            elif level == 4:  # YYYY-MM-DDThh:mm:ss.sss+hh:mm
                                year, month, day = int(match.group(0)[:4]), int(match.group(0)[5:7]), int(match.group(0)[8:10])
                                hour, minute, second = int(match.group(0)[11:13]), int(match.group(0)[14:16]), int(match.group(0)[17:19])
                                millisecond = int(match.group(0)[20:23])
                                timezone = match.group(0)[24:]
                                if not is_valid_date(year, month, day) or not is_valid_time(hour, minute, second, millisecond):
                                    issues.append(f"Trace: {trace_name}, Event: {event_name}, Invalid date/time: {value}")
                            valid = True
                            break
                    if not valid:
                        issues.append(f"Trace: {trace_name}, Event: {event_name}, Invalid timestamp format: {value}")

    if not issues:
        return ["All timestamps are logically valid."]
    
    return issues

def calculate_validity_score(results):
    """
    Calculate the validity score based on assessment results.
    """
    # Extract assessment results
    invalid_attribute_keys = results.get('V1_1_Valid_Key_Names')
    duplicate_attribute_keys = results.get('V1_2_Unique_Attribute_Keys')
    invalid_attribute_values = results.get('V2_1_Data_Type_to_Value_Conformance')
    unsupported_data_types = results.get('V3_1_Allowed_Data_Types')
    timestamp_consistency = results.get('V4_1_Consistent_Timestamp_Format')
    logical_timestamp_issues = results.get('V4_2_Logically_Valid_Timestamps')

    # Calculate individual scores
    attribute_keys_score = 100 if not invalid_attribute_keys else 0
    unique_keys_score = 100 if not duplicate_attribute_keys else 0
    attribute_values_score = 100 if not invalid_attribute_values else 0
    allowed_data_types_score = 100 if all(data == "All data types are supported according to the XES standard" for data in unsupported_data_types) else 0
    timestamp_consistency_score = 100 if all(msg == "The syntax of all timestamps is consistent." for msg in timestamp_consistency) else 0
    logical_timestamp_score = 100 if all(msg == "All timestamps are logically valid." for msg in logical_timestamp_issues) else 0

    # Calculate the overall validity score
    scores = {
        'V1_1_Valid_Key_Names': attribute_keys_score,
        'V1_2_Unique_Attribute_Keys': unique_keys_score,
        'V2_1_Data_Type_to_Value_Conformance': attribute_values_score,
        'V3_1_Allowed_Data_Types': allowed_data_types_score,
        'V4_1_Consistent_Timestamp_Format': timestamp_consistency_score,
        'V4_2_Logically_Valid_Timestamps': logical_timestamp_score
    }

    validity_score = sum(scores.values()) / len(scores)

    # Convert individual scores to percentages
    detailed_scores = {key: score for key, score in scores.items()}
    detailed_scores['V0_Overall_Validity_Score'] = round(validity_score, 2)

    return detailed_scores

def assess_validity(file_path):
    """
    Assess the validity of the XES log.
    Returns a dictionary with the assessment results for validity.
    """
    try:
        log = parse_xes(file_path)

        invalid_attribute_keys = validate_attribute_keys(log)
        duplicate_attribute_keys = validate_unique_keys(file_path)
        invalid_attribute_values = validate_attribute_values(file_path)
        unsupported_data_types = check_allowed_data_types(file_path)
        timestamp_consistency = validate_timestamp_consistency(file_path)
        logical_timestamp_issues = validate_timestamp_logical_constraints(file_path)

        results = {
            'z_status': 'success',
            'V1_1_Valid_Key_Names': invalid_attribute_keys,
            'V1_2_Unique_Attribute_Keys': duplicate_attribute_keys,
            'V2_1_Data_Type_to_Value_Conformance': invalid_attribute_values,
            'V3_1_Allowed_Data_Types': unsupported_data_types,
            'V4_1_Consistent_Timestamp_Format': timestamp_consistency,
            'V4_2_Logically_Valid_Timestamps': logical_timestamp_issues
        }

        validity_scores = calculate_validity_score(results)
        results['V0_Validity_Scores'] = validity_scores

        return results
    
    except Exception as e:
        return {
            'status': 'error',
            'message': str(e)
        }

# Example usage
if __name__ == "__main__":
    file_path = 'path_to_your_xes_file.xes'
    results = assess_validity(file_path)
    print(results)