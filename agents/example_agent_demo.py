"""
Example: Running an Autonomous Agent with P-CAM Hardware Tool
Illustrates how an AI agent uses P-CAM to ground its reasoning in physical reality.
"""

import os
from pcam_agent_tool import PCAMPhysicalSolverTool

# 1. 래피드API 키 설정 (개발자가 자기 키를 넣음)
RAPIDAPI_KEY = os.environ.get("RAPIDAPI_KEY", "YOUR_RAPIDAPI_KEY")

print("==================================================================")
print("  Autonomous AI Agent + NEOMA P-CAM Hardware Tool Integration")
print("==================================================================\n")

try:
    # 2. P-CAM 유료 도구 초기화 (키 없으면 즉시 에러 및 결제 링크 출력)
    pcam_tool = PCAMPhysicalSolverTool(rapidapi_key=RAPIDAPI_KEY)

    print("[1] AI Agent analyzing non-linear structural resonance anomaly...")
    print(
        "[2] AI Agent invoking P-CAM Hardware Tool to find global equilibrium...\n"
    )

    # 3. 에이전트가 스스로 P-CAM 하드웨어를 호출하여 0.85ms 정답 수신
    solution = pcam_tool.run(
        flux_potential_v=0.082,
        gradient_velocity=520,
        gradient_acceleration=16000,
        active_strain=1.55,
    )

    print("---------------- [PHYSICAL CONVERGENCE RESULT] ----------------")
    print(f"Status              : {solution.get('status')}")
    print(f"Hardware Reflex Time: {solution.get('hardware_reflex_ms')} ms")
    print(f"Silicon Seal ID     : {solution.get('hardware_seal_id')}")
    print(f"Attestation Proof   : {solution.get('attestation_proof')[:30]}...")
    print(f"Damping Coefficient : {solution.get('damping_coefficient')}")
    print(f"Physical Insight    : {solution.get('physical_insight')}")
    print("---------------------------------------------------------------")
    print("\n[SUCCESS] AI Agent successfully grounded by physical silicon.")

except ValueError as e:
    print(e)
