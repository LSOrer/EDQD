import unittest
import os
import sys

# Ensure the parent directory is in the sys.path so we can import completeness
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import completeness
import xml.etree.ElementTree as ET

class TestCompleteness(unittest.TestCase):
    def setUp(self):
        # Create a mock XES log
        self.log_xml = '''<?xml version="1.0" encoding="UTF-8" ?>
        <log xes.version="1.0" xes.features="nested-attributes" openxes.version="1.0RC7">
            <extension name="Time" prefix="time" uri="http://www.xes-standard.org/time.xesext"/>
            <extension name="Lifecycle" prefix="lifecycle" uri="http://www.xes-standard.org/lifecycle.xesext"/>
            <extension name="Concept" prefix="concept" uri="http://www.xes-standard.org/concept.xesext"/>
            <classifier name="Event Name" keys="concept:name"/>
            <classifier name="(Event Name AND Lifecycle transition)" keys="concept:name lifecycle:transition"/>
            <string key="concept:name" value="XES Event Log"/>
            <trace>
                <string key="concept:name" value="Guest9723"/>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="start"/>
                    <date key="time:timestamp" value="0025-10-22T17:33:00.000+01:00"/>
                </event>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="complete"/>
                    <date key="time:timestamp" value="0025-10-22T17:33:00.000+01:00"/>
                </event>
            </trace>
            <trace>
                <string key="concept:name" value="Guest9724"/>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="start"/>
                    <date key="time:timestamp" value="0025-10-22T17:48:00.000+01:00"/>
                </event>
            </trace>
        </log>'''
        
        # Save the log to a temporary file for testing
        self.temp_file_path = 'temp_test_log.xes'
        with open(self.temp_file_path, 'w') as f:
            f.write(self.log_xml)

        # Parse the log for internal testing purposes
        self.log = completeness.parse_xes(self.temp_file_path)

    def tearDown(self):
        # Remove the temporary file after testing
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def test_check_missing_values(self):
        missing_values = completeness.check_missing_values(self.log)
        expected_missing_values = {
            'event_attributes': {
                'concept:name': 0,
                'lifecycle:transition': 0,
                'org:resource': 0,
                'time:timestamp': 0
            },
            'trace_attributes': {
                "concept:name": 0                
            }
        }
        self.assertEqual(missing_values, expected_missing_values)

    def test_check_incomplete_traces(self):
        incomplete_traces = completeness.check_incomplete_traces(self.log)
        expected_incomplete_traces = ['Guest9724']
        self.assertEqual(incomplete_traces, expected_incomplete_traces)

    def test_check_attribute_presence(self):
        lifecycle_transition_recorded = completeness.check_attribute_presence(self.log, 'lifecycle:transition')
        org_resource_recorded = completeness.check_attribute_presence(self.log, 'org:resource')
        self.assertTrue(lifecycle_transition_recorded)
        self.assertTrue(org_resource_recorded)

    def test_assess_completeness(self):
        results = completeness.assess_completeness(self.temp_file_path)
        
        expected_results = {
            'status': 'success',
            'missing_values': {
                'event_attributes': {
                    'concept:name': 0,
                    'lifecycle:transition': 0,
                    'org:resource': 0,
                    'time:timestamp': 0
                },
                'trace_attributes': {
                    "concept:name": 0
                }
            },
            'incomplete_traces': ['Guest9724'],
            'lifecycle_transition': 'lifecycle:transition attribute present',
            'org_resource': 'org:resource attribute present'
        }
        
        # Print the full diff if the assertion fails
        self.maxDiff = None
        self.assertEqual(results, expected_results)

if __name__ == '__main__':
    # Run the unit tests
    unittest.main()
