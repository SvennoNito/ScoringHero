function events = detect_kc(eegData, sfreq, opts)
    % DETECT_KC Detect K-complexes in EEG signals using multitaper spectral analysis.
    %
    % Implementation of the method described in:
    %   Oliveira et al. (2020), Expert Systems With Applications 151, 113331.
    %   "Multitaper-based method for automatic k-complex detection in human sleep EEG"
    %
    % USAGE:
    %   events = detect_kc(eegData, sfreq)
    %   events = detect_kc(eegData, sfreq, 'amin', 75, 'dmax_s', 2.0)
    %   events = detect_kc(eegData, sfreq, 'stages', stageVector, 'stageFilter', [2 3])
    %
    % INPUT:
    %   eegData      : [n_channels x n_samples] EEG signal matrix (in µV)
    %   sfreq        : Sampling frequency (Hz)
    %   opts      : Name-value pairs (see below)
    %
    % NAME-VALUE PAIRS:
    %   'amin'       : Minimum peak-to-peak amplitude (µV). Default: 75.0
    %   'dmax_s'     : Maximum KC duration (seconds). Default: 2.0
    %   'q'          : Percentile rank for candidate-region threshold (0–100). Default: 95.0
    %   'fmax'       : Upper frequency bound for KC power (Hz). Default: 3.0
    %   'stages'     : Optional sleep stage vector [1 x n_epochs]. Each value is a stage number.
    %   'stageFilter': Stages to include (e.g., [2 3] for N2 and N3). If empty, all stages included.
    %   'epochLen'   : Epoch length in seconds (required if using stages). Default: 30 seconds.
    %   'outFormat'  : 'seconds' or 'samples'. Default: 'seconds'
    %
    % OUTPUT:
    %   events       : [n_events x 2] matrix of [start end] times.
    %                  Times are in seconds (or samples if outFormat='samples').
    %                  Empty array if no events detected.
    %
    % EXAMPLE:
    %   % Load EEG data
    %   load('eeg_data.mat');  % Contains eegData (channels x samples), sfreq
    %
    %   % Detect KCs with default parameters
    %   events = detect_kc(eegData, 200);
    %
    %   % Detect KCs with custom amplitude threshold and stage filtering
    %   stages = [1 1 2 2 2 3 3 1 1];  % Sleep stages for 9 epochs
    %   events = detect_kc(eegData, 200, 'amin', 100, 'stages', stages, ...
    %                      'stageFilter', [2 3], 'epochLen', 30);

    arguments
        eegData (:,:) {mustBeNumeric}
        sfreq (1,1) {mustBePositive}
        opts.amin (1,1) {mustBePositive} = 75.0
        opts.dmax_s (1,1) {mustBePositive} = 2.0
        opts.q (1,1) {mustBeInRange(opts.q, 0, 100)} = 95.0
        opts.fmax (1,1) {mustBePositive} = 3.0
        opts.stages (:,1) {mustBeInteger} = []
        opts.stageFilter (:,1) {mustBeInteger} = []
        opts.epochLen (1,1) {mustBePositive} = 30
        opts.outFormat char {mustBeMember(opts.outFormat, {'seconds', 'samples'})} = 'seconds'
        opts.plotFlag (1,1) logical = false
        opts.ampUpper (1,1) double = Infs
        opts.ampLower (1,1) double = -Inf
    end

    % Transpose if needed (ensure channels x samples)
    if size(eegData, 1) > size(eegData, 2)
        eegData = eegData';
    end

    n_channels = size(eegData, 1);
    n_samples = size(eegData, 2);

    % Initialize output
    allEvents = [];
    allSignals = {};  % store per-event signal segment for artifact check

    % Process each channel
    for ch = 1:n_channels
        signal = double(eegData(ch, :));

        % Apply stage filtering if provided
        if ~isempty(opts.stages)
            signal = filterByStages(signal, opts.stages, opts.stageFilter, ...
                                   opts.epochLen, sfreq);
            if isempty(signal)
                continue;
            end
        end

        % Detect KCs in this channel
        events_ch = detectKC_singleChannel(signal, sfreq, ...
                                          opts.amin, opts.dmax_s, ...
                                          opts.q, opts.fmax);

        if ~isempty(events_ch)
            for i = 1:size(events_ch, 1)
                n1 = max(1, round(events_ch(i,1) * sfreq));
                n2 = min(length(signal), round(events_ch(i,2) * sfreq));
                allSignals{end+1} = signal(n1:n2);
            end
            allEvents = [allEvents; events_ch];
        end
    end

    % Artifact rejection: remove events with any sample outside [ampLower, ampUpper]
    rejEvents = [];
    if ~isempty(allEvents)
        keep = cellfun(@(s) max(s) <= opts.ampUpper && min(s) >= opts.ampLower, allSignals)';
        n_removed = sum(~keep);
        fprintf('Artifact rejection: removed %d / %d KC events (amp outside [%.0f, %.0f] µV)\n', ...
                n_removed, numel(keep), opts.ampLower, opts.ampUpper);
        rejEvents = allEvents(~keep, :);
        allEvents  = allEvents(keep,  :);
    end

    % Plot overlaid waveforms (kept in dark, rejected in red)
    if opts.plotFlag
        plotKCEvents(eegData, allEvents, rejEvents, sfreq, opts.ampUpper, opts.ampLower);
    end

    % Convert to output format
    if strcmp(opts.outFormat, 'samples')
        allEvents = round(allEvents .* sfreq);
    end

    events = allEvents;
end

%% =========================================================================
% Helper function: Filter signal by sleep stages
% =========================================================================

function signalFiltered = filterByStages(signal, stages, stageFilter, epochLen, sfreq)
    if isempty(stageFilter)
        % No filtering, return full signal
        signalFiltered = signal;
        return;
    end

    n_epochs = length(stages);
    n_samples_epoch = round(epochLen * sfreq);
    n_samples_total = n_epochs * n_samples_epoch;

    % Create mask for included epochs (signal may be longer than n_epochs*n_samples_epoch
    % due to a trailing partial epoch)
    mask = false(1, length(signal));
    for e = 1:n_epochs
        if ismember(stages(e), stageFilter)
            idx_start = (e - 1) * n_samples_epoch + 1;
            idx_end = min(e * n_samples_epoch, length(signal));
            if idx_start <= length(signal)
                mask(idx_start:idx_end) = true;
            end
        end
    end

    % Trim mask to signal length
    mask = mask(1:length(signal));

    % For now, return signal as-is but mark filtered epochs
    % In a more sophisticated implementation, we could split into segments
    signalFiltered = signal;
    signalFiltered(~mask) = 0;  % Zero out non-target stages
end

%% =========================================================================
% Main detection routine for a single channel
% =========================================================================

function events = detectKC_singleChannel(x, sfreq, amin, dmax_s, q, fmax)
    x = double(x(:));  % Ensure column vector
    N = length(x);

    % Scale all sample-based parameters to actual sfreq
    L       = max(2, round(sfreq));                  % 1 s window
    delta_j = max(1, round(0.05 * sfreq));           % 0.05 s step
    delta_f = 4.0;                                   % Hz, spectral resolution (fixed)
    Ishort  = max(1, round(0.5 * sfreq / delta_j));  % ≈ 0.5 s of spectrogram cols
    Ibackg  = 10 * Ishort;                           % ≈ 5 s
    Lsmth   = max(1, round(0.15 * sfreq));           % 0.15 s smoothing
    Lbackg  = delta_j * Ibackg;                      % 5 s amplitude background
    Dmax    = round(dmax_s * sfreq);                 % max duration in samples

    % 1. Bandpass filter
    x = bandpassFilter(x, sfreq);

    % 2. Multitaper spectrogram
    [SG, J, R] = computeSpectrogram(x, sfreq, L, delta_j, delta_f);

    % 3. Candidate regions
    regions = identifyCandidateRegions(SG, J, R, sfreq, fmax, Ishort, Ibackg, q);
    if isempty(regions)
        events = [];
        return;
    end

    % 4. Candidate KC marking
    KCcand = markKCCandidates(x, N, regions, delta_j, Lsmth, Lbackg);
    if isempty(KCcand)
        events = [];
        return;
    end

    % 5 + 6. Elimination
    KCout = eliminateCandidates(x, regions, KCcand, delta_j, amin, Dmax);

    % Convert sample indices to seconds
    if isempty(KCout)
        events = [];
    else
        events = KCout / sfreq;
    end
end

%% =========================================================================
% Internal helpers
% =========================================================================

function y = bandpassFilter(x, sfreq)
    % Bandpass filter: 0.3 - 35 Hz, 4th order Butterworth
    low = 0.3;
    high = 35.0;
    nyq = sfreq / 2.0;

    Wn = [low/nyq, min(high/nyq, 0.999)];
    [b, a] = butter(4, Wn, 'bandpass');

    y = filtfilt(b, a, x);
end

function y = centralMovingAverage(x, window)
    % Central moving average using uniform filter
    window = max(1, round(window));
    y = movmean(x, window, 'Endpoints', 'shrink');
end

function sigma = centralMovingStd(x, window)
    % Central moving standard deviation
    window = max(1, round(window));
    mean_x = movmean(x, window, 'Endpoints', 'shrink');
    mean_x2 = movmean(x.^2, window, 'Endpoints', 'shrink');
    sigma = sqrt(max(0, mean_x2 - mean_x.^2));
end

function p = nextPow2(n)
    % Next power of 2 >= n
    p = 2^ceil(log2(n));
end

function [SG, J, R] = computeSpectrogram(x, sfreq, L, delta_j, delta_f)
    % Multitaper spectrogram computation
    N = length(x);
    TW = (L * delta_f) / (2.0 * sfreq);
    K = max(1, round(2 * TW) - 1);

    % Compute DPSS tapers
    [tapers, ~] = dpss(L, TW, K);  % MATLAB returns shape (L, K)

    R = nextPow2(L);
    J = ceil(N / delta_j);
    half = R / 2 + 1;

    SG = zeros(half, J);

    for j = 1:J
        start = (j - 1) * delta_j + 1;  % Convert to 1-based indexing
        seg = zeros(L, 1);
        avail = min(L, N - start + 1);
        if avail > 0
            seg(1:avail) = x(start:start + avail - 1);
        end

        SW = zeros(half, 1);
        for k = 1:K
            tapered = tapers(:, k) .* seg;
            fft_out = fft(tapered, R);
            fft_out = fft_out(1:half);
            SW = SW + (1.0 / sfreq) * abs(fft_out).^2 / K;
        end

        SG(:, j) = SW;
    end

    SG = 10.0 * log10(SG + 1.0);
end

function regions = identifyCandidateRegions(SG, J, R, sfreq, fmax, Ishort, Ibackg, q)
    % Identify candidate regions in spectrogram
    freqs = (0:(size(SG, 1)-1))' * (sfreq / R);

    % Sum delta-band power per column
    mask = freqs <= fmax;
    C = sum(SG(mask, :), 1)';  % Column sum -> column vector

    % Short and background moving averages
    Cshort = centralMovingAverage(C, Ishort);
    Cbackg = centralMovingAverage(C, Ibackg);

    % Difference
    Cdiff = Cshort - Cbackg;

    % Threshold at q-th percentile
    thresh = prctile(Cdiff, q);

    above = Cdiff >= thresh;
    regions = [];
    in_region = false;
    j1 = 0;

    for j = 1:J
        if above(j) && ~in_region
            j1 = j;
            in_region = true;
        elseif ~above(j) && in_region
            regions = [regions; j1, j - 1];
            in_region = false;
        end
    end

    if in_region
        regions = [regions; j1, J];
    end
end

function KCcand = markKCCandidates(x, N, regions, delta_j, Lsmth, Lbackg)
    % Mark candidate KCs based on amplitude envelope
    x_smth = centralMovingAverage(x, Lsmth);
    x_backg = centralMovingAverage(x, Lbackg);
    sigma = centralMovingStd(x, Lbackg);

    A_inf = x_backg - sigma;
    A_sup = x_backg + sigma;

    % Find transition points: where x_smth crosses x_backg downward
    above = x_smth >= x_backg;
    transitions_idx = find(above(1:end-1) & ~above(2:end));

    KCcand = [];

    for i = 1:length(transitions_idx) - 1
        n1 = transitions_idx(i);
        n2 = transitions_idx(i + 1);

        % Check if n1 falls inside any candidate region
        in_region = false;
        for r = 1:size(regions, 1)
            j1 = regions(r, 1);
            j2 = regions(r, 2);
            if n1 >= j1 * delta_j && n1 <= j2 * delta_j
                in_region = true;
                break;
            end
        end

        if ~in_region
            continue;
        end

        % Amplitude condition: x_smth must dip below A_inf AND rise above A_sup
        if n1 < 1 || n2 > N
            continue;
        end

        seg_smth = x_smth(n1:n2);
        seg_inf = A_inf(n1:n2);
        seg_sup = A_sup(n1:n2);

        if any(seg_smth <= seg_inf) && any(seg_smth >= seg_sup)
            KCcand = [KCcand; n1, n2];
        end
    end
end

function KCout = eliminateCandidates(x, regions, KCcand, delta_j, amin, Dmax)
    % Eliminate KC candidates based on amplitude and duration

    % One candidate per region: keep the one with max peak-to-peak amplitude
    KCmax = [];
    for r = 1:size(regions, 1)
        j1 = regions(r, 1);
        j2 = regions(r, 2);

        % Find all candidates in this region
        pool = [];
        for c = 1:size(KCcand, 1)
            n1 = KCcand(c, 1);
            if n1 >= j1 * delta_j && n1 <= j2 * delta_j
                pool = [pool; KCcand(c, :)];
            end
        end

        if isempty(pool)
            continue;
        end

        % Find the one with max peak-to-peak amplitude
        [~, idx_max] = max(arrayfun(@(k) ptp(x(pool(k, 1):pool(k, 2))), 1:size(pool, 1)));
        KCmax = [KCmax; pool(idx_max, :)];
    end

    % Filter by amplitude >= amin AND duration < Dmax
    KCout = [];
    for i = 1:size(KCmax, 1)
        n1 = KCmax(i, 1);
        n2 = KCmax(i, 2);
        amp = ptp(x(n1:n2));
        dur = n2 - n1;

        if amp >= amin && dur < Dmax
            KCout = [KCout; n1, n2];
        end
    end
end

function p = ptp(x)
    % Peak-to-peak amplitude
    p = max(x) - min(x);
end

%% =========================================================================
% Stacked plot of detected KC events
% =========================================================================

function plotKCEvents(eegData, events_s, rejEvents_s, sfreq, ampUpper, ampLower)
    n_samples = size(eegData, 2);
    signal    = double(eegData(1, :));
    pad_s     = 0.5;

    figure('Name', 'Detected K-complexes');
    ax = axes;
    hold(ax, 'on');

    function plotGroup(evts, color)
        for i = 1:size(evts, 1)
            n_start = max(1, round((evts(i,1) - pad_s) * sfreq));
            n_end   = min(n_samples, round((evts(i,2) + pad_s) * sfreq));
            seg     = signal(n_start:n_end);
            t       = (0:length(seg)-1) / sfreq - pad_s;
            h = plot(ax, t, seg, 'Color', color, 'LineWidth', 0.8);
            h.Color(4) = 0.3;
        end
    end

    plotGroup(rejEvents_s, [0.85 0.15 0.15]);  % red  = rejected
    plotGroup(events_s,    [0.15 0.15 0.15]);  % dark = kept

    all_events = [events_s; rejEvents_s];
    max_dur = 0;
    if ~isempty(all_events)
        max_dur = max(all_events(:,2) - all_events(:,1));
    end

    xline(ax, 0, 'b--', 'KC onset');
    if isfinite(ampUpper)
        yline(ax, ampUpper, 'r:', sprintf('%.0f µV', ampUpper));
    end
    if isfinite(ampLower)
        yline(ax, ampLower, 'r:', sprintf('%.0f µV', ampLower));
    end
    xlabel(ax, 'Time relative to KC onset (s)');
    ylabel(ax, 'Amplitude (\muV)');
    title(ax, sprintf('K-complexes: %d kept (dark), %d rejected (red) — ch 1', ...
                      size(events_s, 1), size(rejEvents_s, 1)));
    if max_dur > 0
        xlim(ax, [-pad_s, max_dur + pad_s]);
    end
    box(ax, 'off');
    hold(ax, 'off');
end
