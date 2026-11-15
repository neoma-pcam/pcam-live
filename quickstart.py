import os
from neoma_pcam import PCAMClient

# Set PCAM_RAPIDAPI_KEY (Free 2,000 calls/mo) or test directly against live gateway
api_key = os.getenv("PCAM_RAPIDAPI_KEY")
client = PCAMClient(api_key=api_key) if api_key else PCAMClient(base_url="https://api.neoma-pcam.com/docs")

res = client.solve_ising(
    fields=[1.5, -1.2, 0.8, 2.0],
    couplings=[(0, 1, -1.0), (1, 2, 1.5), (2, 3, 1.2)],
)
print("Converged Spins:", res["spins"])
print("Ground-State Energy:", res["ground_state_energy"])
print("Hardware Attestation Seal:", res["hardware_seal_id"])