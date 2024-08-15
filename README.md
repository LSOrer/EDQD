# The Event Data Quality Dashboard (EDQD)

## About:
The Event Data Quality Dashboard (EDQD) is a tool designed to help users evaluate the quality of event logs used in process mining and other data-driven analysis. Event logs are crucial for understanding processes within organizations, but the quality of these logs can significantly impact the accuracy and reliability of any insights derived from them.

**Key Features of EDQD:**
- **Assessment of Data Quality Dimensions:** EDQD evaluates event logs across five main dimensions of data quality:
  - **Completeness:** Ensures that all necessary data is recorded without omissions, such as missing values or events.
  - **Accuracy:** Checks for errors like duplicate events, incorrect timestamps, or traces that might belong to a different process.
  - **Interpretability:** Assesses whether the data is easy to understand and interpret, checking for issues like coarse timestamps or unclear activity names.
  - **Relevancy:** Identifies and flags events that are irrelevant or noise, which could skew the analysis.
  - **Validity:** Verifies that the data conforms to expected formats and types, ensuring logical consistency.
- **Visual Representation:** The dashboard provides a visual summary of the data quality assessment, with color-coded boxes representing each quality dimension. Green indicates high quality, yellow indicates some issues, and red indicates significant problems.
- **Detailed Analysis:** Users can click on each quality dimension box to view detailed information about the specific issues found, allowing them to understand and address the data quality problems effectively.
- **User-Friendly Interface:** The dashboard is designed to be intuitive, making it easy for users, even those without a technical background, to assess and improve the quality of their event logs.

In essence, the Event Data Quality Dashboard is a powerful tool for organizations looking to ensure the reliability of their process mining and data analysis by providing a clear, actionable overview of the quality of their event logs.


## Running the code with Docker

Make a new directory and download the code to it.
Navigate to the directory and run: 
```
docker build -t edqd .
```
to build the image. After that you run:
```
docker run -p 5001:80 edqd
```
to expose the port 5001 for the container.

Now you can open a browser of your choice and access the dashboard with the url:
```
http://127.0.0.1:5001/
```
