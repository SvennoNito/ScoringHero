import numpy as np
from widgets import AnnotationContainer

def events_to_ui(ui, events):

    ui.AnnotationContainer = [
        AnnotationContainer(colorindex=counter, label=f"F{counter}")
        for counter in range(13)
    ]   

    if len(events) > 0:
        event_digits = [item["digit"] for item in events]
        for event_digit in set(event_digits):
            container_index = np.where(np.array(event_digits) == event_digit)[0].tolist()
            for container in np.array(events)[container_index]:
                ui.AnnotationContainer[event_digit].label = container["event"]
                ui.AnnotationContainer[event_digit].borders.append(
                    [container["start"], container["end"]]
                )
                ui.AnnotationContainer[event_digit].epochs.append(container["epoch"])     
