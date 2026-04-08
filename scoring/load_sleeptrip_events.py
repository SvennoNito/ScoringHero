import csv


def load_sleeptrip_events(filename):
    """Load a SleepTrip events CSV file (_events.csv).

    Returns:
        events: list of dicts with keys: event, start, stop, duration, channel
        unique_labels: ordered list of unique event type names
    """
    events = []
    with open(filename, "r", newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        for row in reader:
            events.append({
                "event": row["event"].strip(),
                "start": float(row["start"]),
                "stop": float(row["stop"]),
                "duration": float(row["duration"]),
                "channel": row["channel"].strip(),
            })

    unique_labels = list(dict.fromkeys(e["event"] for e in events))
    return events, unique_labels
