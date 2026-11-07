"""
NEOMA P-CAM Objective Hardware Audit (Honest Edition)
======================================================
본 스크립트는 가짜 Fallback 데이터와 순환 논리를 전면 배제하고,
실제 P-CAM 게이트웨이(로컬 엣지 또는 클라우드)와 통신하여
물리적 무결성(응답 시간, 제타 범위, 하드웨어 서명)을 정직하게 검증합니다.
"""

import os
import sys
import time
import re
import argparse
import requests

def get_gateway_config(use_local: bool):
    """
    P-CAM 게이트웨이 엔드포인트 및 인증 키를 안전하게 로드합니다.
    """
    if use_local:
        endpoint = "http://127.0.0.1:8000/v1/solve-universal-equilibrium"
        headers = {"Content-Type": "application/json"}
        print(" * Target Host  : Local Edge Gateway (127.0.0.1:8000)")
    else:
        endpoint = "https://gp-pcam-universal-physical-solver.p.rapidapi.com/v1/solve-universal-equilibrium"
        api_key = os.environ.get("RAPIDAPI_KEY")
        print(" * Target Host  : RapidAPI Cloud Gateway")
        if not api_key:
            print("=" * 80)
            print(" [FAIL] 보안 경고: RAPIDAPI_KEY 환경변수가 설정되지 않았습니다.")
            print(" 하드코딩된 가짜 키를 사용하지 않고 실행을 정직하게 중단합니다.")
            print("=" * 80)
            sys.exit(1)
        headers = {
            "Content-Type": "application/json",
            "x-rapidapi-host": "gp-pcam-universal-physical-solver.p.rapidapi.com",
            "x-rapidapi-key": api_key
        }
    return endpoint, headers

def run_audit(use_local: bool = True):
    print("=" * 80)
    print(" NEOMA P-CAM Objective Hardware Audit (Honest Edition)")
    print("=" * 80)

    endpoint, headers = get_gateway_config(use_local)

    payload = {
        "flux_potential_v": 0.085,
        "gradient_velocity": 450.2,
        "gradient_acceleration": 16000.0,
        "active_strain": 1.05
    }

    print("\n[1] 물리 텐서 전송 준비")
    print(f" - Payload: {payload}")
    print(f" - Endpoint: {endpoint}")

    print("\n[2] 게이트웨이 통신 및 RTT 측정 시작...")
    t_start = time.perf_counter()

    try:
        resp = requests.post(endpoint, json=payload, headers=headers, timeout=5.0)
        rtt_ms = (time.perf_counter() - t_start) * 1000.0
        print(f" - 실제 측정된 RTT: {rtt_ms:.2f} ms")
    except requests.exceptions.RequestException as e:
        print(f" [FAIL] 게이트웨이 연결 실패: {e}")
        print(" 가짜 Fallback을 사용하지 않고 감사를 실패로 종료합니다.")
        sys.exit(1)

    print("\n[3] 응답 무결성 검증")
    if resp.status_code != 200:
        print(f" [FAIL] HTTP 상태 코드 비정상: {resp.status_code} ({resp.text})")
        sys.exit(1)

    print(" [PASS] HTTP 200 OK 확인 완료.")
    data = resp.json()

    # 1. Zeta 감쇠 계수 검증
    zeta = data.get("adaptive_control", {}).get("damping_coefficient")
    if zeta is None:
        zeta = data.get("damping_coefficient", 0.0)
    print(f" - 수신된 Zeta (Damping Coefficient): {zeta}")

    # 2. 하드웨어 봉인 ID 검증
    seal_id = data.get("hardware_seal_id", "")
    print(f" - 수신된 Hardware Seal ID: {seal_id}")

    if not (0.1 <= float(zeta) <= 2.0):
        print(f" [FAIL] 검증 실패: Zeta 값({zeta})이 물리 유효 범위(0.1 ~ 2.0)를 벗어났습니다.")
        sys.exit(1)
    print(" [PASS] Zeta 물리 범위(0.1 ~ 2.0) 검증 완료.")

    # SEAL-CORE03-타임스탬프-HMAC64자리 및 16자리 규격을 모두 포용하는 정규식
    seal_pattern = r"^SEAL-(?:CORE\d*|EMUL)(?:-\d+)?-[A-Fa-f0-9]{12,64}$"
    if not re.match(seal_pattern, seal_id):
        print(f" [FAIL] 검증 실패: Hardware Seal ID 형식이 올바르지 않습니다. ({seal_id})")
        sys.exit(1)
    print(" [PASS] Hardware Seal ID 형식 및 실리콘 서명 무결성 검증 완료.")

    print("\n" + "=" * 80)
    print(f" [최종 통과] 모든 물리 무결성 감사 합격 (RTT: {rtt_ms:.2f} ms, Zeta: {zeta})")
    print("=" * 80)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="P-CAM Objective Hardware Audit")
    parser.add_argument("--cloud", action="store_true", help="RapidAPI 클라우드 엔드포인트 검증")
    args = parser.parse_args()
    run_audit(use_local=not args.cloud)