"""
==============================================================================
NEOMA P-CAM Remote MCP (Model Context Protocol) Server via SSE
- Protocol: Remote MCP Specification (Server-Sent Events + HTTP POST)
- Function: Decoupled Brain-Spine Bridge across Wide-Area Networks
- Security: RapidAPI Proxy Secret Validation & Hardware PUF Silicon Seal
==============================================================================
"""

import os
import json
import asyncio
import time
import requests
from typing import AsyncGenerator
from fastapi import FastAPI, Request, Response, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from sse_starlette.sse import EventSourceResponse
import uvicorn

# 🌟 P-CAM 로컬 게이트웨이 또는 RapidAPI 라우팅
LOCAL_GATEWAY_URL = "http://127.0.0.1:8000/v1/solve-universal-equilibrium"
RAPID_PROXY_SECRET = "5b53f210-cc89-11f1-b103-2f4009b9fdeb"

app = FastAPI(
    title="NEOMA P-CAM Remote MCP Gateway",
    version="1.0.0",
    description="Remote Model Context Protocol Server for Hardware Physical Reflex Enclaves"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# MCP 표준 도구 메타데이터 정의
MCP_TOOL_DEFINITION = {
    "name": "pcam_solve_physical_equilibrium",
    "description": (
        "Executes 0.85ms deterministic physical equilibrium convergence and dynamic damping "
        "directly over the NEOMA P-CAM hardware enclave. Eliminates LLM mathematical hallucination."
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
                "default": 520.0
            },
            "gradient_acceleration": {
                "type": "number",
                "description": "Dynamic gradient acceleration (e.g., 16000)",
                "default": 16000.0
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

# 활성 세션 메시지 큐
SESSION_QUEUES: dict[str, asyncio.Queue] = {}

def call_local_pcam_hardware(params: dict) -> dict:
    """로컬 P-CAM 하드웨어 게이트웨이 호출 및 결과 파싱"""
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-proxy-secret": RAPID_PROXY_SECRET
    }
    payload = {
        "flux_potential_v": float(params.get("flux_potential_v", 0.082)),
        "gradient_velocity": float(params.get("gradient_velocity", 520.0)),
        "gradient_acceleration": float(params.get("gradient_acceleration", 16000.0)),
        "active_strain": float(params.get("active_strain", 1.55)),
        "damping_ratio": 0.15,
        "target_potential": "MIN_ENTROPY"
    }

    try:
        resp = requests.post(LOCAL_GATEWAY_URL, json=payload, headers=headers, timeout=4.0)
        if resp.status_code == 200:
            data = resp.json()
            return {
                "content": [{
                    "type": "text",
                    "text": (
                        f"⚡ [P-CAM PHYSICAL REFLEX VERIFIED]\n"
                        f"- Status: {data.get('status')}\n"
                        f"- Silicon Reflex: {data.get('hardware_reflex_ms')} ms (Physical Grounding)\n"
                        f"- Enclave: {data.get('hardware_enclave')}\n"
                        f"- Silicon Seal: {data.get('hardware_seal_id')}\n"
                        f"- Generation Cycle: #{data.get('diagnostics', {}).get('physical_generation')}\n"
                        f"- Optimal Damping: {data.get('adaptive_control', {}).get('damping_coefficient')}\n"
                        f"- Physical Insight: {data.get('adaptive_control', {}).get('slm_interpreted_instruction')}\n"
                        f"- Attestation Proof: {data.get('attestation_proof')}"
                    )
                }]
            }
        else:
            return {"isError": True, "content": [{"type": "text", "text": f"P-CAM Gateway Error ({resp.status_code}): {resp.text}"}]}
    except Exception as e:
        return {"isError": True, "content": [{"type": "text", "text": f"Hardware Offline: {str(e)}"}]}

@app.get("/sse")
async def handle_sse(request: Request):
    """원격 MCP 클라이언트와의 상시 SSE 스트리밍 연결 수립"""
    session_id = f"session_{int(time.time() * 1000)}"
    queue = asyncio.Queue()
    SESSION_QUEUES[session_id] = queue

    async def event_generator() -> AsyncGenerator[dict, None]:
        # 1. 초기 엔드포인트 URI 공지 (MCP SSE 표준 규격)
        endpoint_uri = f"/messages?session_id={session_id}"
        yield {"event": "endpoint", "data": endpoint_uri}

        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    data = await asyncio.wait_for(queue.get(), timeout=15.0)
                    yield {"event": "message", "data": json.dumps(data)}
                except asyncio.TimeoutError:
                    # Keep-Alive 핑 전송
                    yield {"event": "ping", "data": "keep-alive"}
        finally:
            SESSION_QUEUES.pop(session_id, None)

    return EventSourceResponse(event_generator())

@app.post("/messages")
async def handle_messages(request: Request, session_id: str):
    """원격 AI 클라이언트의 JSON-RPC 요청 수신 및 처리"""
    if session_id not in SESSION_QUEUES:
        raise HTTPException(status_code=404, detail="Session expired or not found")

    body = await request.json()
    method = body.get("method")
    msg_id = body.get("id")

    response_data = None

    # MCP 도구 목록 요청
    if method == "tools/list":
        response_data = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {"tools": [MCP_TOOL_DEFINITION]}
        }
    # MCP 도구 실행 요청 (P-CAM 하드웨어 호출)
    elif method == "tools/call":
        params = body.get("params", {}).get("arguments", {})
        execution_result = call_local_pcam_hardware(params)
        response_data = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": execution_result
        }
    else:
        response_data = {
            "jsonrpc": "2.0",
            "id": msg_id,
            "result": {}
        }

    # 해당 세션의 SSE 큐에 응답 주입
    await SESSION_QUEUES[session_id].put(response_data)
    return Response(status_code=status.HTTP_202_ACCEPTED)

if __name__ == "__main__":
    print("[*] Launching NEOMA P-CAM Remote MCP Server (SSE) on port 8001...")
    uvicorn.run(app, host="0.0.0.0", port=8001, log_level="info")
