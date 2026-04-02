function jsonData = updateJSONWithEvents(jsonInput, events, srate)
    % updateJSONWithEvents(jsonInput, events, srate)
    %
    % Updates JSON data with event information, counting occurrences of each label.
    %
    % Inputs:
    %   jsonInput: Either a path to a JSON file (string) or a JSON structure.
    %   events: A struct array or table containing event data. Required fields:
    %           - start (in samples)
    %           - duration (in seconds)
    %           - key (string, 'A', 'F1', 'F2', ..., 'F12')
    %           - label (string, event label, e.g., 'Artifact', 'Spindle')
    %   srate: Sampling rate of the data (samples per second).
    %
    % The JSON data should have the structure provided in the prompt.

    % Load or use the JSON data
    if ischar(jsonInput)
        jsonData = jsondecode(fileread(jsonInput));
    elseif isstruct(jsonInput)
        jsonData = jsonInput;
    else
        error('jsonInput must be a string (file path) or a struct.');
    end

    % Extract epoch duration
    epochDuration = jsonData{1}(1).end - jsonData{1}(1).start; % Assuming all epochs have same duration

    % Extract epoch start times
    epochStartTimes = [jsonData{1}.start];
    epochEndTimes = epochStartTimes + epochDuration;

    % Initialize counters for each event label
    labelCounters = containers.Map();

    % Loop through events
    for ievent = 1:length(events)
        event = events(ievent);

        % Name of event
        eventLabel = event.label; 

        % Determine digit based on key
        eventKey = event.key;

        if strcmp(eventKey, 'A')
            eventDigit = 0;
        else
            eventDigit = str2double(eventKey(2:end)); % Extract number from 'F1', 'F2', etc.
        end

        % Convert sample start to time start
        eventStart = event.start / srate;

        % Calculate time end
        eventEnd = eventStart + event.duration;

        % Determine epochs
        eventEpochs = find(eventStart >= epochStartTimes & eventStart < epochEndTimes) : find(eventEnd > epochStartTimes & eventEnd <= epochEndTimes);

        % Get or initialize counter for this label
        if isKey(labelCounters, eventLabel)
            counter = labelCounters(eventLabel) + 1;
        else
            counter = 1;
        end

        % Update counter for this label
        labelCounters(eventLabel) = counter;

        % Create event struct
        newEvent = struct( ...
            'key', eventKey, ...
            'event', eventLabel, ...
            'digit', eventDigit, ...
            'counter', counter, ...
            'epoch', eventEpochs, ...
            'start', eventStart, ...
            'end', eventEnd ...
        );

        % Append to JSON data
        jsonData{2}(end + 1) = newEvent;
    end
    %
    % % Update name
    % [basename] = fileparts(jsonFilePath)
    %
    % % Write updated JSON file
    % fid = fopen([basename '_withEvents.json'], 'w');
    % fprintf(fid, '%s', jsonencode(jsonData, 'PrettyPrint', true));
    % fclose(fid);
end