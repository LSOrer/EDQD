import unittest
import os
import sys

# Ensure the parent directory is in the sys.path so we can import completeness and xes_parser
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import completeness
import xes_parser

class TestCompleteness(unittest.TestCase):
    def setUp(self):
        # Create a mock XES log with all completeness issues
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
                    <string key="concept:name" value=""/>
                    <string key="lifecycle:transition" value="start"/>
                    <date key="time:timestamp" value="2022-01-01T00:00:00.000+01:00"/>
                </event>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="complete"/>
                    <date key="time:timestamp" value="2022-01-01T03:00:00.000+01:00"/>
                </event>
            </trace>
            <trace>
                <string key="concept:name" value="Guest9724"/>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="start"/>
                    <date key="time:timestamp" value="2022-01-01T02:00:00.000+01:00"/>
                </event>
            </trace>
            <trace>
                <string key="concept:name" value="Guest9725"/>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="start"/>
                    <date key="time:timestamp" value="2022-01-01T03:00:00.000+01:00"/>
                </event>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="complete"/>
                    <date key="time:timestamp" value="2022-01-01T04:00:00.000+01:00"/>
                </event>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="complete"/>
                    <date key="time:timestamp" value="2022-01-02T05:00:00.000+01:00"/>
                </event>
            </trace>
            <trace>
                <string key="concept:name" value="Guest9726"/>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="start"/>
                    <date key="time:timestamp" value="2022-01-01T05:00:00.000+01:00"/>
                </event>
                <event>
                    <string key="org:resource" value="Tom"/>
                    <string key="concept:name" value="Check-in table"/>
                    <string key="lifecycle:transition" value="complete"/>
                    <date key="time:timestamp" value="2022-01-01T04:00:00.000+01:00"/>
                </event>
            </trace>
            <event>
                <string key="org:resource" value="manager"/>
                <string key="concept:name" value="D"/>
                <string key="lifecycle:transition" value="complete"/>
                <date key="time:timestamp" value="2022-01-05T00:00:00.000+01:00"/>
            </event>
        </log>'''
        
        # Save the log to a temporary file for testing
        self.temp_file_path = 'temp_test_log.xes'
        with open(self.temp_file_path, 'w') as f:
            f.write(self.log_xml)

        # Parse the log for internal testing purposes
        self.log = xes_parser.parse_xes(self.temp_file_path)

    def tearDown(self):
        # Remove the temporary file after testing
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

    def test_check_missing_values(self):
        missing_values = completeness.check_missing_values(self.log)
        expected_missing_values = {
            'event_attributes': {
                'concept:name': 1,
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

    def test_check_unrecorded_traces(self):
        unrecorded_traces = completeness.check_unrecorded_traces(self.log, pattern_threshold=1, time_gap_factor=3)
        expected_unrecorded_traces = {
            "Trace Pattern Anomalies": [],
            "Significant Time Gaps": []
        }
        self.assertEqual(unrecorded_traces, expected_unrecorded_traces)

    def test_find_orphan_events(self):
        orphan_events = completeness.find_orphan_events(self.temp_file_path)
        expected_orphan_events = [
            {
                'concept:name': 'D',
                'lifecycle:transition': 'complete',
                'org:resource': 'manager',
                'time:timestamp': '2022-01-05T00:00:00.000+01:00'
            }
        ]
        self.assertEqual(orphan_events, expected_orphan_events)

    def test_find_misordered_traces(self):
        misordered_traces = completeness.find_misordered_traces(self.log)
        expected_misordered_traces = ['Guest9726']
        self.assertEqual(misordered_traces, expected_misordered_traces)

    def test_assess_completeness(self):
        results = completeness.assess_completeness(self.temp_file_path)
        
        expected_results = {
            'status': 'success',
            'missing_values': {
                'event_attributes': {
                    'concept:name': 1,
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
            'org_resource': 'org:resource attribute present',
            'unrecorded_traces': {
                "Trace Pattern Anomalies": [],
                "Significant Time Gaps": []
            },
            'orphan_events': [
                {
                    'concept:name': 'D',
                    'lifecycle:transition': 'complete',
                    'org:resource': 'manager',
                    'time:timestamp': '2022-01-05T00:00:00.000+01:00'
                }
            ],
            'misordered_traces': ['Guest9726']
        }
        
        # Print the full diff if the assertion fails
        self.maxDiff = None
        self.assertEqual(results, expected_results)

if __name__ == '__main__':
    # Run the unit tests
    unittest.main()
