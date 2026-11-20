"""
NEOMA P-CAM 64-Spin Physical Ising Solver - QCentroid Solver Adapter
Official QCentroid Platform Solver Specification
"""
import os
import json
import logging
import urllib.request
import urllib.error

logger = logging.getLogger("qcentroid-user-log")

DEFAULT_GATEWAY_URL = "https://api.neoma-pcam.com/v1/ising/solve"
MAX_SPINS = 64


def _normalize_gateway_url(url: str) -> str:
    """Ensures target endpoint path ends with /v1/ising/solve."""
    url = url.strip().rstrip("/")
    if url.endswith("/v1/ising/solve") or url.endswith("/ising/solve"):
        return url
    return f"{url}/v1/ising/solve"


def _qubo_to_ising(qubo_matrix):
    """
    Converts an N x N QUBO matrix into equivalent Ising fields (h) and couplings (J).
    Binary x_i in {0, 1} mapped to spin s_i in {-1, +1} via x_i = (1 + s_i) / 2.
    E_QUBO = x^T Q x
    H_PCAM = -sum_{i < j} J_ij s_i s_j - sum_i h_i s_i
    """
    n = len(qubo_matrix)
    if n > MAX_SPINS:
        raise ValueError(f"NEOMA P-CAM supports up to {MAX_SPINS} spins (got {n}).")
    if n < 1:
        raise ValueError("qubo_matrix must contain at least 1 variable.")

    # Symmetrize Q: Q_tilde[i][j] = Q[i][j] + Q[j][i] for i != j
    fields = [0.0] * n
    couplings = []

    for i in range(n):
        diag_q = float(qubo_matrix[i][i])
        off_diag_sum = 0.0
        for j in range(n):
            if i != j:
                w = float(qubo_matrix[i][j]) + float(qubo_matrix[j][i])
                off_diag_sum += w
                if i < j and abs(w) > 1e-12:
                    # In P-CAM: -J_ij = w / 4 => J_ij = -w / 4
                    couplings.append([i, j, round(-w / 4.0, 6)])

        # -h_i = diag_q / 2 + off_diag_sum / 4 => h_i = -(diag_q / 2 + off_diag_sum / 4)
        fields[i] = round(-(diag_q / 2.0 + off_diag_sum / 4.0), 6)

    return n, fields, couplings


def _maxcut_to_ising(adj_matrix):
    """
    Converts an N x N graph adjacency matrix into anti-ferromagnetic Ising couplings.
    J_ij = -W_ij / 2, with zero external magnetic field (h_i = 0.0).
    Energies minimize when adjacent nodes take opposite spins (s_i != s_j).
    """
    n = len(adj_matrix)
    if n > MAX_SPINS:
        raise ValueError(f"NEOMA P-CAM supports up to {MAX_SPINS} spins (got {n}).")
    if n < 1:
        raise ValueError("adj_matrix must contain at least 1 node.")

    fields = [0.0] * n
    couplings = []

    for i in range(n):
        for j in range(i + 1, n):
            w = float(adj_matrix[i][j])
            if abs(w) > 1e-12:
                # Anti-ferromagnetic coupling: J_ij = -W_ij / 2
                j_val = round(-w / 2.0, 6)
                couplings.append([i, j, j_val])

    return n, fields, couplings


def run(input_data: dict, solver_params: dict, extra_arguments: dict) -> dict:
    """
    QCentroid official solver entry point.
    
    Parameters:
        input_data (dict): Problem definition. Supports:
            - Max-Cut: {"adj_matrix": [[...], ...]}
            - QUBO: {"qubo_matrix": [[...], ...]}
            - Native Ising: {"fields": [...], "couplings": [[i, j, w], ...], "num_spins": N}
        solver_params (dict): Solver tuning parameters (e.g., timeout, initial_spins, api_key, gateway_url).
        extra_arguments (dict): Platform injection arguments (e.g., NEOMA_API_KEY, NEOMA_GATEWAY_URL).
        
    Returns:
        dict: Standardized solver response dictionary containing hardware attestation.
    """
    logger.info("Initializing NEOMA P-CAM QCentroid Solver Adapter...")

    if not isinstance(input_data, dict):
        raise TypeError("input_data must be a dictionary.")
    solver_params = solver_params or {}
    extra_arguments = extra_arguments or {}

    # 1. Resolve Gateway URL
    raw_url = (
        extra_arguments.get("NEOMA_GATEWAY_URL")
        or solver_params.get("NEOMA_GATEWAY_URL")
        or extra_arguments.get("gateway_url")
        or solver_params.get("gateway_url")
        or os.getenv("NEOMA_GATEWAY_URL")
        or DEFAULT_GATEWAY_URL
    )
    gateway_url = _normalize_gateway_url(str(raw_url))
    logger.info("Target Gateway URL: %s", gateway_url)

    # 2. Resolve API Key
    api_key = (
        extra_arguments.get("NEOMA_API_KEY")
        or extra_arguments.get("api_key")
        or solver_params.get("NEOMA_API_KEY")
        or solver_params.get("api_key")
        or os.getenv("NEOMA_API_KEY")
        or os.getenv("NEOMA_DIRECT_API_KEYS", "").split(",")[0].strip()
        or os.getenv("PCAM_MCP_API_KEY")
        or ""
    ).strip()

    # 3. Process Input Data and map to 64-Spin Ising problem
    if "adj_matrix" in input_data:
        problem_type = "max_cut"
        num_spins, fields, couplings = _maxcut_to_ising(input_data["adj_matrix"])
        logger.info("Mapped Max-Cut graph (%d nodes, %d edges) to anti-ferromagnetic Ising core.", num_spins, len(couplings))

    elif "qubo_matrix" in input_data:
        problem_type = "qubo"
        num_spins, fields, couplings = _qubo_to_ising(input_data["qubo_matrix"])
        logger.info("Mapped QUBO matrix (%d variables, %d couplings) to physical Ising core.", num_spins, len(couplings))

    elif "fields" in input_data and "couplings" in input_data:
        problem_type = "ising"
        fields = [float(x) for x in input_data["fields"]]
        num_spins = int(input_data.get("num_spins") or solver_params.get("num_spins") or len(fields))
        if num_spins > MAX_SPINS:
            raise ValueError(f"NEOMA P-CAM supports up to {MAX_SPINS} spins (got {num_spins}).")
        if len(fields) != num_spins:
            raise ValueError(f"fields length ({len(fields)}) does not match num_spins ({num_spins}).")

        # Couplings normalization: accept [[i, j, w]] or [{"i": i, "j": j, "j_ij": w}]
        raw_couplings = input_data["couplings"]
        couplings = []
        for c in raw_couplings:
            if isinstance(c, (list, tuple)) and len(c) >= 3:
                couplings.append([int(c[0]), int(c[1]), float(c[2])])
            elif isinstance(c, dict):
                i = int(c.get("i", 0))
                j = int(c.get("j", 0))
                w = float(c.get("j_ij", c.get("weight", c.get("value", c.get("J", 0.0)))))
                couplings.append([i, j, w])
        logger.info("Prepared Native Ising problem (%d spins, %d couplings).", num_spins, len(couplings))

    else:
        raise ValueError("input_data must contain either 'adj_matrix', 'qubo_matrix', or both 'fields' and 'couplings'.")

    # 4. Construct Payload
    payload = {
        "num_spins": num_spins,
        "fields": fields,
        "couplings": couplings,
    }
    if "initial_spins" in solver_params:
        payload["initial_spins"] = solver_params["initial_spins"]

    # 5. Build HTTP Request
    headers = {
        "Content-Type": "application/json",
        "User-Agent": "QCentroid-Neoma-Pcam-Adapter/1.0",
    }
    if api_key:
        headers["x-neoma-api-key"] = api_key

    timeout_sec = float(solver_params.get("timeout") or extra_arguments.get("timeout") or 15.0)

    logger.info("Submitting %d-spin problem to NEOMA P-CAM silicon core at %s...", num_spins, gateway_url)
    req_body = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(gateway_url, data=req_body, headers=headers, method="POST")

    try:
        with urllib.request.urlopen(req, timeout=timeout_sec) as resp:
            resp_body = resp.read().decode("utf-8")
            resp_data = json.loads(resp_body)
    except urllib.error.HTTPError as http_err:
        err_body = ""
        try:
            err_body = http_err.read().decode("utf-8")
        except Exception:
            pass
        logger.error("NEOMA P-CAM Enclave HTTP error: %d %s - %s", http_err.code, http_err.reason, err_body)
        raise RuntimeError(f"NEOMA P-CAM HTTP Error {http_err.code}: {err_body or http_err.reason}") from http_err
    except Exception as exc:
        logger.error("NEOMA P-CAM Connection Failed: %s", exc)
        raise RuntimeError(f"NEOMA P-CAM Connection Failed: {exc}") from exc

    # 6. Parse and format response
    raw_spins = resp_data.get("spins", [])
    binary_solution = [1 if int(s) > 0 else 0 for s in raw_spins]
    partitions = list(binary_solution)  # Max-Cut node partition (0 or 1)

    output = {
        "problem_type": problem_type,
        "spins": raw_spins,
        "binary_solution": binary_solution,
        "partitions": partitions,
        "ground_state_energy": resp_data.get("ground_state_energy"),
        "magnetization": resp_data.get("magnetization"),
        "hardware_reflex_ms": resp_data.get("hardware_reflex_ms"),
        "hardware_seal_id": resp_data.get("hardware_seal_id"),
        "puf_dynamic_seal": resp_data.get("puf_dynamic_seal"),
        "firewall_guard": resp_data.get("firewall_guard"),
        "status": resp_data.get("status", "hardware_active"),
        "num_spins": num_spins,
        "couplings_count": resp_data.get("couplings_count", len(couplings)),
        "relaxation_sweeps": resp_data.get("relaxation_sweeps"),
        "equilibrium_converged": resp_data.get("equilibrium_converged", True),
        "domain": resp_data.get("domain", "Ising-64Spin-Hamiltonian"),
        "zeta": resp_data.get("zeta"),
    }

    logger.info(
        "P-CAM Convergence achieved in %s ms (SEAL: %s, PUF: %s, Status: %s)",
        output.get("hardware_reflex_ms"),
        output.get("hardware_seal_id"),
        output.get("puf_dynamic_seal"),
        output.get("status"),
    )
    return output
