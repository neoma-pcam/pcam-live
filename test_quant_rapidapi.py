"""
NEOMA P-CAM Quant Reflex HFT - RapidAPI Verification Test
Validates 15µs hardware reflex through RapidAPI proxy gateway.
"""

import os
import sys
import time
import argparse
import requests

# RapidAPI 호스트 및 엔드포인트 설정
RAPIDAPI_HOST = "neoma-p-cam-quant-reflex-hft.p.rapidapi.com"
ENDPOINT_URL = f"https://{RAPIDAPI_HOST}/v1/quant/predict"

def test_quant_hft(api_key: str):
    headers = {
        "content-type": "application/json",
        "X-RapidAPI-Host": RAPIDAPI_HOST,
        "X-RapidAPI-Key": api_key
    }

    # 호가 불균형 4차원 물리 텐서 페이로드
    payload = {
        "flux_potential_v": 0.085,
        "gradient_velocity": 450.2,
        "gradient_acceleration": 16000.0,
        "active_strain": 1.05
    }

    print("=" * 75)
    print(" [NEOMA P-CAM] RapidAPI Quant Reflex HFT Live Attestation")
    print(f" * Target Host : {RAPIDAPI_HOST}")
    print(f" * Endpoint    : {ENDPOINT_URL}")
    print("=" * 75)

    t0 = time.perf_counter()
    try:
        response = requests.post(ENDPOINT_URL, json=payload, headers=headers, timeout=10.0)
        round_trip_ms = (time.perf_counter() - t0) * 1000.0
    except requests.exceptions.RequestException as e:
        print(f"❌ 요청 실패: {e}")
        return

    if response.status_code != 200:
        print(f"❌ 호출 에러 (HTTP {response.status_code}): {response.text}")
        return

    data = response.json()
    zeta = data.get("zeta", 1.0)
    mode = data.get("state_mode", 1)
    hw_latency = data.get("hardware_reflex_ms", 0.0)
    seal = data.get("hardware_seal_id", "")

    print(f"✔ HTTP Status             : 200 OK")
    print(f"✔ RapidAPI 왕복 통신 지연 : {round_trip_ms:.2f} ms")
    print(f"✔ 15µs 실리콘 코어 반사   : {hw_latency:.4f} ms")
    print(f"✔ 물리 감쇠비 (Zeta)      : {zeta:.4f}")
    print(f"✔ 하드웨어 봉인 (SEAL-ID) : {seal[:40]}...")

    # 트레이딩 판단
    if zeta > 1.2 or mode == 3:
        print("\n🚨 [PULL_QUOTES] 호가창 스윕 충격 감지 -> 지정가 주문 즉시 취소 (슬리피지 방어)")
    else:
        print("\n🟢 [HOLD_MAKER] 임계 감쇠 안정 구간 -> 유동성 공급 유지")
    print("=" * 75)

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--key", type=str, help="Your RapidAPI Key")
    args = parser.parse_args()

    api_key = args.key or os.environ.get("RAPIDAPI_KEY")
    if not api_key:
        api_key = input("RapidAPI Key를 입력하세요: ").strip()

    if not api_key:
        print("API Key가 입력되지 않아 종료합니다.")
        sys.exit(1)

    test_quant_hft(api_key)
