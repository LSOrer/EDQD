document.getElementById('uploadForm').addEventListener('submit', function(event) {
    event.preventDefault();
    var formData = new FormData(this);

    // Show the loading animation
    document.getElementById('loading').style.display = 'block';
    document.getElementById('results').style.display = 'none';

    fetch('/upload', {
        method: 'POST',
        body: formData
    }).then(response => response.json())
      .then(data => {
        displayResults(data);
      }).catch(error => {
        console.error('Error:', error);
    }).finally(() => {
        // Hide the loading animation
        document.getElementById('loading').style.display = 'none';
        document.getElementById('results').style.display = 'block';
      });
});

function displayResults(data) {
    var resultsDiv = document.getElementById('results');
    resultsDiv.innerHTML = '<h1>Event Data Quality Dashboard</h1>';

    var qualityDimensions = [
        { 
            name: 'Completeness', 
            score: data.Completeness?.completeness_scores?.overall_completeness_score || 0, 
            details: data.Completeness,
            status: data.Completeness.status,
            subScores: data.Completeness.status === 'success' ? {
                'C1 Missing Values': data.Completeness.completeness_scores.present_attribute_values,
                'C2 Incomplete Traces': data.Completeness.completeness_scores.complete_traces,
                'C4 Unrecorded Traces': (data.Completeness.unrecorded_traces.trace_pattern_anomalies.length === 0 && data.Completeness.unrecorded_traces.unusual_inter_trace_time_gaps.length === 0) ? 100 : 90,
                'C5 Unrecorded Events': data.Completeness.unrecorded_events.unusual_inter_event_time_gaps.length === 0 ? 100 : 90,
                'C6 Orphan Events': data.Completeness.completeness_scores.associated_events,
                'C7 Disordered Traces': data.Completeness.completeness_scores.ordered_traces
            } : {}
        },
        { 
            name: 'Accuracy', 
            score: data.Accuracy?.accuracy_scores?.overall_accuracy_score || 0, 
            details: data.Accuracy,
            status: data.Accuracy.status,
            subScores: data.Accuracy.status === 'success' ? {
                'A1 Unrealistic Timestamps': data.Accuracy.accuracy_scores.timestamp_accuracy,
                'A2 Trace belongs to a diffrent process': data.Accuracy.potential_traces_of_a_different_process.length === 0 ? 100 : 90,
                'A3-1 Trace Duplicates': data.Accuracy.accuracy_scores.duplicate_traces,
                'A3-2 Event Duplicates': data.Accuracy.accuracy_scores.duplicate_events
            } : {}
        },
        { 
            name: 'Interpretability', 
            score: data.Interpretability?.interpretability_scores?.overall_interpretability_score || 0, 
            details: data.Interpretability,
            status: data.Interpretability.status,
            subScores: data.Interpretability.status === 'success' ? {
                'I1-1 Coarse Timestamps': data.Interpretability.interpretability_scores.timestamp_coarseness,
                'I1-2 Coarse Resources': data.Interpretability.interpretability_scores.resource_information,
                'I1-3 Coarse Activity Names': data.Interpretability.interpretability_scores.activity_name_granularity
            } : {}
        },
        { 
            name: 'Relevancy', 
            score: data.Relavency?.overall_relevancy_score || 0, 
            details: data.Relavency,
            status: data.Relavency.status,
            subScores: data.Relavency.status === 'success' ? {
                'R1-1 Noise Events': data.Relavency.overall_relevancy_score
            } : {}
        },
        { 
            name: 'Validity', 
            score: data.Validity?.validity_scores?.overall_validity_score || 0, 
            details: data.Validity,
            status: data.Validity.status,
            subScores: data.Validity.status === 'success' ? {
                'V1-1 Valid Key Name': data.Validity.validity_scores.valid_attribute_keys,
                'V1-2 Unique Attribute Keys': data.Validity.validity_scores.unique_keys,
                'V2-1 Data Type to Value Conformance': data.Validity.validity_scores.valid_attribute_values,
                'V3-1 Allowed Data Types': data.Validity.validity_scores.allowed_data_types,
                'V4-1 Consistent Timestamp Format': data.Validity.validity_scores.timestamp_consistency,
                'V4-2 Logically Valid Timestamps': data.Validity.validity_scores.logical_timestamps
            } : {}
        }
    ];

    qualityDimensions.forEach((dimension, index) => {
        var colorClass = dimension.status === 'success' ? getColorClass(dimension.score, 'main') : 'white-main';

        var dimensionBox = document.createElement('div');
        dimensionBox.className = `box ${colorClass}`;
        dimensionBox.innerHTML = `${dimension.name}<br>${dimension.score}%`;
        dimensionBox.dataset.index = index;

        var subScoresDiv = document.createElement('div');
        subScoresDiv.style.marginTop = '20px';

        var descriptions = {
            'C1 Missing Values': 'This indicator checks if important attributes are missing in traces or events. Missing values may lead to incomplete or unreliable data.',
            'C2 Incomplete Traces': 'Evaluates whether any traces in the event log are incomplete, meaning that crucial transitions or events may be missing.',
            'C4 Unrecorded Traces': 'Identifies traces that are potentially unrecorded due to anomalies in patterns or unusual time gaps between traces.',
            'C5 Unrecorded Events': 'Detects missing events within traces, typically identified by unusually large time gaps between consecutive events.',
            'C6 Orphan Events': ' Identifies events that are not properly linked to any trace, leading to potential data inconsistencies.',
            'C7 Disordered Traces': 'This metric checks whether events within traces are ordered correctly based on timestamps.',

            'A1 Unrealistic Timestamps': 'Assesses whether there are any timestamps that are in the future or unrealistically far in the past, which would suggest inaccuracies in logging.',
            'A2 Trace belongs to a diffrent process': 'Flags traces that may belong to a different process based on deviations in the event name sequence.',
            'A3-1 Trace Duplicates': 'Identifies traces that have been duplicated in the log, leading to inflated or incorrect analysis.',
            'A3-2 Event Duplicates': 'Detects duplicate events within the same trace, which could result from logging errors or system misbehavior.',

            'I1-1 Coarse Timestamps': 'This metric checks if the timestamps are too coarse, meaning they might only record days without accounting for hours, minutes, or seconds.',
            'I1-2 Coarse Resources': 'Verifies if the resource-related attributes (such as the responsible entity for an event) are recorded in a detailed or overly general way.',
            'I1-3 Coarse Activity Names': 'Detects whether activity names are too vague or not descriptive enough to allow for meaningful process analysis.',

            'R1-1 Noise Events':'Identifies events that are deemed irrelevant to the process under investigation, such as system notifications or maintenance logs that do not contribute to process understanding.',

            'V1-1 Valid Key Name': 'Checks if attribute keys conform to the XES standard, ensuring they do not contain illegal characters like line breaks, tabs, or carriage returns.',
            'V1-2 Unique Attribute Keys': 'Verifies that attribute keys are unique within their respective containers, avoiding potential conflicts or confusion in analysis.',
            'V2-1 Data Type to Value Conformance': 'Ensures that the values of attributes match their expected data types, e.g., integers should contain numeric values, and booleans should be either true or false.',
            'V3-1 Allowed Data Types': 'Validates that only allowed data types (such as string, date, integer, float, etc.) are present in the event log.',
            'V4-1 Consistent Timestamp Format': 'Assesses whether timestamps are formatted consistently across the entire log, avoiding issues with differing time formats.',
            'V4-2 Logically Valid Timestamps': 'Checks if timestamps follow logical constraints, such as valid days, hours, and months (e.g., no 25th hour or 45th month).'
        };

        if (dimension.status === 'success') {
            Object.keys(dimension.subScores).forEach(subScoreName => {
                var subScoreValue = dimension.subScores[subScoreName];
                var subColorClass = getColorClass(subScoreValue, 'small');
                var subScoreBox = document.createElement('div');
                subScoreBox.className = `small-box ${subColorClass}`;
                subScoreBox.innerHTML = `${subScoreName}`;
                subScoreBox.setAttribute('data-description', descriptions[subScoreName]);
                subScoresDiv.appendChild(subScoreBox);
            });
        } else {
            subScoresDiv.innerHTML = '<div class="small-box white-small">Error</div>';
        }

        dimensionBox.appendChild(subScoresDiv);

        var detailsButton = document.createElement('button');
        detailsButton.className = 'details-button';
        detailsButton.innerHTML = 'Details';
        detailsButton.onclick = () => openModal(dimension);
        dimensionBox.appendChild(detailsButton);

        resultsDiv.appendChild(dimensionBox);
    });
}

function getColorClass(score, type) {
    if (type === 'main') {
        if (score === 100) return 'green-main';
        if (score >= 80) return 'yellow-main';
        return 'red-main';
    } else {
        if (score === 100) return 'green-small';
        if (score >= 80) return 'yellow-small';
        return 'red-small';
    }
}

// Modal functionality
var modal = document.getElementById("detailsModal");
var span = document.getElementsByClassName("close")[0];

function openModal(dimension) {
    var modalContent = document.getElementById("modalContent");
    if (dimension.status === 'success') {
        modalContent.innerHTML = generateDetailTable(dimension.details);
    } else {
        modalContent.innerHTML = `<p><strong>Error:</strong> ${dimension.details.message}</p>`;
    }
    modal.style.display = "block";
}

span.onclick = function() {
    modal.style.display = "none";
}

window.onclick = function(event) {
    if (event.target == modal) {
        modal.style.display = "none";
    }
}

function generateDetailTable(details) {
    let html = '';
    Object.keys(details).forEach(key => {
        if (details[key] !== null && details[key] !== undefined) {
            if (typeof details[key] === 'object') {
                html += `<h3>${key}</h3>`;
                html += '<table>';
                Object.keys(details[key]).forEach(subKey => {
                    html += `<tr><th>${subKey}</th><td>${JSON.stringify(details[key][subKey], null, 2)}</td></tr>`;
                });
                html += '</table>';
            } else {
                html += `<p><strong>${key}:</strong> ${details[key]}</p>`;
            }
        } else {
            html += `<p><strong>${key}:</strong> No data available</p>`;
        }
    });
    return html;
}