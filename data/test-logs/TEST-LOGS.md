# Synthetic Test Logs for Quality Assessments
This subfolder contains synthetic test logs designed to verify the functionality of the data quality assessments implemented in the dashboard. Each log file addresses a specific data quality problem that might occur in event logs. The logs are annotated with comments to indicate where issues arise.

## Overview
This project includes several indicators that check for specific data quality problems in event logs. Each synthetic test log corresponds to a particular indicator and contains scenarios that trigger the respective quality checks. By using these logs, you can ensure that the quality assessments are functioning correctly and accurately identifying data quality issues.

## Usage
1. Download Logs: Clone the repository and navigate to the subfolder containing the synthetic test logs.
2. Run Assessments: Use each log to test the corresponding quality assessment function in your dashboard. The logs are named and commented to indicate the specific issues they are designed to trigger.
3. Verify Functionality: Ensure that the quality assessment functions correctly identify the issues in the synthetic logs.

## Example
Here is an example of how to use the synthetic logs to verify the duplicate events detection function:

1. Download the log file duplicate_events_log.xes.
2. Run the find_duplicate_events function with this log as input.
3. Verify that the function returns the trace names where duplicate events are present as indicated in the log comments.

## Contributions
Contributions are welcome! If you identify additional quality issues or have suggestions for improving the synthetic logs, please submit a pull request or open an issue.

## License
This project is licensed under the MIT License.
