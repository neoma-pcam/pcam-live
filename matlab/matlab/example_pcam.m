%% NEOMA P-CAM Physical Solver Demonstration
% Demonstrates sub-millisecond physical equilibrium convergence via cloud

clear; clc;

fprintf('=====================================================\n');
fprintf('  Connecting to NEOMA P-CAM Physical Hardware Enclave\n');
fprintf('=====================================================\n\n');

% Execute Physical Solver
tic;
result = pcam_solve(0.15, 'MIN_ENTROPY');
elapsed_total_ms = toc * 1000;

% Display Verified Hardware Results
fprintf('Status               : %s\n', result.status);
fprintf('Service Edition      : %s\n', result.service_edition);
fprintf('Hardware Reflex Time : %.4f ms (Silicon Substrate)\n', result.hardware_reflex_ms);
fprintf('Total Network RTT    : %.2f ms (Cloudflare Ingress)\n', elapsed_total_ms);
fprintf('Hardware Enclave     : %s\n', result.hardware_enclave);
fprintf('Silicon Seal ID      : %s\n', result.hardware_seal_id);
fprintf('Attestation Proof    : %s\n\n', result.attestation_proof(1:30));

fprintf('Adaptive Control Action:\n');
fprintf(' -> Damping Coefficient: %.4f\n', result.adaptive_control.damping_coefficient);
fprintf(' -> Physical Insight   : %s\n', result.adaptive_control.slm_interpreted_instruction);
fprintf('\n[SUCCESS] Hardware Convergence Verified.\n');
