function response = pcam_solve(damping_ratio, target_potential, apiKey)
% PCAM_SOLVE Connects MATLAB to NEOMA P-CAM Physical Hardware Solver via Cloud
%
% Syntax:
%   res = pcam_solve()
%   res = pcam_solve(0.15, 'MIN_ENTROPY')
%   res = pcam_solve(0.15, 'MIN_ENTROPY', 'YOUR_RAPIDAPI_KEY')
%
% Description:
%   Offloads complex non-linear dynamic equilibrium calculations directly to 
%   the NEOMA P-CAM physical hardware enclave (0.85ms deterministic reflex).
%
% Output:
%   response - Struct containing hardware attestation, reflex time (ms), 
%              silicon seal ID, and verified adaptive damping control.
%
% Author: NEOMA Systems Inc.
% Gateway: https://api.neoma-pcam.com

    if nargin < 1 || isempty(damping_ratio)
        damping_ratio = 0.15;
    end
    if nargin < 2 || isempty(target_potential)
        target_potential = 'MIN_ENTROPY';
    end
    if nargin < 3
        apiKey = '';
    end

    payload = struct(...
        'flux_potential_v', 0.082, ...
        'gradient_velocity', 520, ...
        'gradient_acceleration', 16000, ...
        'active_strain', 1.55, ...
        'damping_ratio', damping_ratio, ...
        'target_potential', target_potential ...
    );

    % Endpoint selection
    if isempty(apiKey)
        % Direct Gateway (Evaluation Tier)
        url = 'https://api.neoma-pcam.com/v1/solve-universal-equilibrium';
        options = weboptions('MediaType', 'application/json', 'Timeout', 10);
    else
        % RapidAPI Production Tier
        url = 'https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium';
        options = weboptions('MediaType', 'application/json', ...
            'HeaderFields', {'X-RapidAPI-Key', apiKey; 'X-RapidAPI-Host', 'gp-pcam-universal-physical-solver.p.rapidapi.com'}, ...
            'Timeout', 10);
    end

    try
        % Execute Physical Co-processing via Cloud
        response = webwrite(url, payload, options);
    catch ME
        error('P-CAM Hardware Solver Connection Failed: %s', ME.message);
    end
end
