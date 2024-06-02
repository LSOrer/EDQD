from datetime import datetime

def analyze_event_time_gaps(log, factor):

    significant_gaps = []
    info = []
    for i, trace in enumerate(log):
        timestamps = [datetime.fromisoformat(event['time:timestamp']) for event in trace['events'] if 'time:timestamp' in event]
        if len(timestamps) > 1:
            gaps = [(timestamps[i+1] - timestamps[i]).total_seconds() for i in range(len(timestamps) - 1)]
            mean_gap = sum(gaps) / len(gaps)
            trace_log = {
                'trace_index': i,
                'trace_name': trace['attributes'].get('concept:name', 'Unnamed trace'),
                'gaps': gaps,
                'mean_gap': mean_gap
            }

            info.append(trace_log)
            for j, gap in enumerate(gaps):
                if gap > factor * mean_gap:
                    significant_gaps.append(i)

    return significant_gaps, info

def analyze_inter_trace_gaps(log, factor):
        trace_times = []
        
        # Extract the opening and closing time of each trace
        for trace in log:
            events = [datetime.fromisoformat(event['time:timestamp']) for event in trace['events'] if 'time:timestamp' in event]
            if events:
                opening_time = events[0]
                closing_time = events[-1]
                trace_times.append((opening_time, closing_time))
        
        # Sort traces by opening time
        trace_times.sort(key=lambda x: x[0])
        
        inter_trace_gaps = []
        trace_pairs = []
        for i in range(1, len(trace_times)):
            previous_closing_time = trace_times[i-1][1]
            current_opening_time = trace_times[i][0]
            
            # Only consider non-overlapping traces
            if current_opening_time > previous_closing_time:
                gap = (current_opening_time - previous_closing_time).total_seconds()
                inter_trace_gaps.append(gap)
                trace_pairs.append((i-1, i))
        
        mean_gap = sum(inter_trace_gaps) / len(inter_trace_gaps) if inter_trace_gaps else 0
        
        significant_gaps = []
        for i, gap in enumerate(inter_trace_gaps):
            if gap > factor * mean_gap:
                trace1_index, trace2_index = trace_pairs[i]
                trace1_name = log[trace1_index]['attributes'].get('concept:name', 'Unnamed trace')
                trace2_name = log[trace2_index]['attributes'].get('concept:name', 'Unnamed trace')
                significant_gaps.append({
                    'Large Gap between': f"{trace1_name} and {trace2_name}",
                    'gap': gap
                })
        
        return significant_gaps, mean_gap