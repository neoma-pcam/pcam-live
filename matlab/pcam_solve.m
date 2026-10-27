function response = pcam_solve(damping_ratio, target_potential, apiKey)
% PCAM_SOLVE Connects MATLAB to NEOMA P-CAM Physical Solver via RapidAPI Gateway
%
% Syntax:
%   res = pcam_solve(0.15, 'MIN_ENTROPY', 'YOUR_RAPIDAPI_KEY')
%
% Author: NEOMA Systems Inc.
% Gateway: RapidAPI Shielded Production

    if nargin < 1 || isempty(damping_ratio)
        damping_ratio = 0.15;
    end
    if nargin < 2 || isempty(target_potential)
        target_potential = 'MIN_ENTROPY';
    end
    if nargin < 3 || isempty(apiKey)
        error(['RapidAPI Key is required to access the physical hardware enclave.\n' ...
               'Please get your 50 free calls key at:\n' ...
               'https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver']);
    end

    payload = struct(...
        'flux_potential_v', 0.082, ...
        'gradient_velocity', 520, ...
        'gradient_acceleration', 16000, ...
        'active_strain', 1.55, ...
        'damping_ratio', damping_ratio, ...
        'target_potential', target_potential ...
    );

    % 🌟 403 에러 원천 차단: 래피드API 정식 게이트웨이 경유
    url = 'https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium';
    options = weboptions('MediaType', 'application/json', ...
        'HeaderFields', {'X-RapidAPI-Key', apiKey; 'X-RapidAPI-Host', 'gp-pcam-universal-physical-solver.p.rapidapi.com'}, ...
        'Timeout', 10);

    try
        response = webwrite(url, payload, options);
    catch ME
        error('P-CAM Hardware Solver Execution Failed: %s', ME.message);
    end
end
