import unittest
import sys
import os

# Ensure the parent directory is in the sys.path so we can import completeness
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import completeness
from pm4py.objects.log.obj import EventLog, Trace, Event
from pm4py.objects.log.exporter.xes import exporter as xes_exporter

class TestCompleteness(unittest.TestCase):
    def setUp(self):
        # Create a mock XES log
        self.log = EventLog()

        # Create a complete trace
        trace1 = Trace()
        event1 = Event({'concept:name': 'Start', 'lifecycle:transition': 'complete', 'org:resource': 'User1'})
        event2 = Event({'concept:name': 'End', 'lifecycle:transition': 'complete', 'org:resource': 'User2'})
        trace1.append(event1)
        trace1.append(event2)
        trace1.attributes['concept:name'] = 'Trace 1'

        # Create an incomplete trace
        trace2 = Trace()
        event3 = Event({'concept:name': 'Start', 'lifecycle:transition': 'start', 'org:resource': 'User3'})
        trace2.append(event3)
        trace2.attributes['concept:name'] = 'Trace 2'

        self.log.append(trace1)
        self.log.append(trace2)

        # Save the log to a temporary file for testing
        self.temp_file_path = 'temp_test_log.xes'
        xes_exporter.apply(self.log, self.temp_file_path)

    def tearDown(self):
        # Remove the temporary file after testing
        if os.path.exists(self.temp_file_path):
            os.remove(self.temp_file_path)

#    def test_check_missing_values(self):
#        missing_values = completeness.check_missing_values(self.log)
#        expected_missing_values = {
#            'trace_attributes': {},
#            'event_attributes': {
#                'concept:name': 0,
#                'lifecycle:transition': 0,
#                'org:resource': 0
#            }
#        }
#        self.assertEqual(missing_values, expected_missing_values)

    def test_check_incomplete_traces(self):
        incomplete_traces = completeness.check_incomplete_traces(self.log)
        expected_incomplete_traces = ['Trace 2']
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
                    'org:resource': 0
                },
                'trace_attributes': {
                    "concept:name": 0
                }
            },
            'incomplete_traces': ['Trace 2'],
            'lifecycle_transition': 'lifecycle:transition attribute present',
            'org_resource': 'org:resource attribute present'
        }
        
        # Print the full diff if the assertion fails
        self.maxDiff = None
        self.assertEqual(results, expected_results)

if __name__ == '__main__':
    
    # Run the unit tests
    unittest.main()