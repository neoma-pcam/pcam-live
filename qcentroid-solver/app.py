"""
Local verification script for NEOMA P-CAM QCentroid Solver Adapter.
Executes a 4-node Max-Cut square graph (C_4) against the live silicon enclave.
"""
import os
import sys
import json
import logging
from pathlib import Path

# Configure basic console logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")

# Load environment variables from .env if present
def load_env_file():
    candidates = [
        Path(".env"),
        Path("../.env"),
        Path(__file__).parent / ".env",
        Path(__file__).parent.parent / ".env",
    ]
    for p in candidates:
        if p.is_file():
            try:
                for line in p.read_text(encoding="utf-8").splitlines():
                    line = line.strip()
                    if not line or line.startswith("#") or "=" not in line:
                        continue
                    k, v = line.split("=", 1)
                    k = k.strip()
                    v = v.strip().strip("'\"")
                    if k and k not in os.environ:
                        os.environ[k] = v
            except Exception:
                pass
            break

load_env_file()

# Ensure current directory is on Python path
sys.path.insert(0, str(Path(__file__).parent))
import qcentroid

def main():
    # 4-node Max-Cut square graph (C_4 ring: (0,1), (1,2), (2,3), (3,0))
    adj_matrix = [
        [0, 1, 0, 1],
        [1, 0, 1, 0],
        [0, 1, 0, 1],
        [1, 0, 1, 0],
    ]

    input_data = {
        "adj_matrix": adj_matrix,
    }

    solver_params = {
        "timeout": 15.0,
    }

    extra_arguments = {}

    print("Submitting 4-node Max-Cut square graph to NEOMA P-CAM via QCentroid adapter...")
    result = qcentroid.run(input_data, solver_params, extra_arguments)

    print("\n================== QCentroid Solver Result ==================")
    print(json.dumps(result, indent=2))
    print("=============================================================\n")

    # Verification checks
    status = result.get("status")
    reflex_ms = result.get("hardware_reflex_ms")
    puf_seal = result.get("puf_dynamic_seal")
    spins = result.get("spins")
    partitions = result.get("partitions")

    print(f"Verification Summary:")
    print(f"  * Status            : {status}")
    print(f"  * Hardware Reflex   : {reflex_ms} ms")
    print(f"  * PUF Dynamic Seal  : {puf_seal}")
    print(f"  * Spins             : {spins}")
    print(f"  * Partitions        : {partitions}")

    if status == "hardware_active" and reflex_ms is not None and reflex_ms < 1.0 and puf_seal:
        print("\n[SUCCESS] Live silicon hardware verification passed!")
    else:
        print("\n[FAIL] Live silicon verification checks not satisfied.")
        sys.exit(1)

if __name__ == "__main__":
    main()
