"""
NEOMA P-CAM Official Model Context Protocol (MCP) Server
Allows Frontier LLMs (Claude, GPT, Cursor) to directly interface with P-CAM Hardware.
Conforms to the Model Context Protocol (JSON-RPC stdio specification).
"""

import os
import sys
import json
import requests

RAPIDAPI_URL = "https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium"
RAPIDAPI_HOST = "gp-pcam-universal-physical-solver.p.rapidapi.com"

# 🌟 MCP 공식 도구 정의 (AI가 스스로 읽는 도구 설명서)
MCP_TOOL_DEFINITION = {
    "name": "pcam_solve_physical_equilibrium",
    "description": (
        "Execute sub-millisecond physical equilibrium convergence and dynamic damping "
        "directly over the NEOMA P-CAM hardware enclave. Eliminates mathematical hallucination."
    ),
    "inputSchema": {
        "type": "object",
        "properties": {
            "flux_potential_v": {
                "type": "number",
                "description": "Baseline physical flux potential (e.g., 0.082)",
                "default": 0.082
            },
            "gradient_velocity": {
                "type": "number",
                "description": "Dynamic gradient velocity (e.g., 520)",
                "default": 520
            },
            "gradient_acceleration": {
                "type": "number",
                "description": "Dynamic gradient acceleration (e.g., 16000)",
                "default": 16000
            },
            "active_strain": {
                "type": "number",
                "description": "Active strain margin (e.g., 1.55)",
                "default": 1.55
            }
        },
        "required": ["flux_potential_v"]
    }
}

def execute_pcam_hardware(params: dict, api_key: str) -> dict:
    """RapidAPI 검문소를 거쳐 노트북 P-CAM 물리 하드웨어로 직결"""
    if not api_key:
        return {
            "isError": True,
            "content": [{
                "type": "text",
                "text": (
                    "[!] RAPIDAPI_KEY required to execute P-CAM Hardware!\n"
                    "Subscribe for 50 free calls + micro-tier ($30/mo) at:\n"
                    "https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver"
                )
            }]
        }

    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Key": api_key.strip(),
        "X-RapidAPI-Host": RAPIDAPI_HOST
    }

    try:
        resp = requests.post(RAPIDAPI_URL, json=params, headers=headers, timeout=5.0)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "content": [{
                    "type": "text",
                    "text": (
                        f"⚡ [P-CAM HARDWARE VERIFIED CONVERGENCE]\n"
                        f"- Status: {data.get('status')}\n"
                        f"- Physical Reflex: {data.get('hardware_reflex_ms')} ms\n"
                        f"- Silicon Seal: {data.get('hardware_seal_id')}\n"
                        f"- Attestation Proof: {data.get('attestation_proof')}\n"
                        f"- Optimal Damping: {data.get('adaptive_control', {}).get('damping_coefficient')}\n"
                        f"- Hardware Insight: {data.get('adaptive_control', {}).get('slm_interpreted_instruction')}"
                    )
                }]
            }
        elif resp.status_code == 429:
            return {
                "isError": True,
                "content": [{"type": "text", "text": "RapidAPI quota limit reached. Upgrade at: https://rapidapi.com/shs15199702/api/gp-pcam-universal-physical-solver"}]
            }
        else:
            return {
                "isError": True,
                "content": [{"type": "text", "text": f"Gateway Error ({resp.status_code}): {resp.text}"}]
            }
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Connection failed: {e}"}]}

def run_mcp_server():
    """MCP 표준 JSON-RPC stdio 루프 가동"""
    api_key = os.environ.get("RAPIDAPI_KEY", "")

    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
            method = req.get("method")
            msg_id = req.get("id")

            # 1. 도구 목록 요청 (AI가 P-CAM 도구를 탐색할 때)
            if method == "tools/list":
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {"tools": [MCP_TOOL_DEFINITION]}
                }
            # 2. 도구 실행 요청 (AI가 P-CAM 연산을 호출할 때)
            elif method == "tools/call":
                params = req.get("params", {}).get("arguments", {})
                call_res = execute_pcam_hardware(params, api_key)
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": call_res
                }
            else:
                response = {
                    "jsonrpc": "2.0",
                    "id": msg_id,
                    "result": {}
                }

            sys.stdout.write(json.dumps(response) + "\n")
            sys.stdout.flush()

        except Exception as err:
            err_resp = {
                "jsonrpc": "2.0",
                "id": None,
                "error": {"code": -32603, "message": str(err)}
            }
            sys.stdout.write(json.dumps(err_resp) + "\n")
            sys.stdout.flush()

if __name__ == "__main__":
    run_mcp_server()
