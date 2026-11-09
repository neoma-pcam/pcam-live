"""
CCXT LOB Shock Damping Example
Simulates real-time order book sweep defense via P-CAM 15µs Silicon Core.
"""

import sys
import time
from pathlib import Path

# 상위 폴더(pcam-live) 경로를 모듈 검색 경로에 자동 등록
ROOT_DIR = Path(__file__).resolve().parent.parent
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from pcam_quant import PCAMShockShield

def main():
    print("=" * 75)
    print(" [NEOMA P-CAM] CCXT LOB Shock Shield & Slippage Defense Test")
    print("=" * 75)

    # 1. 쉴드 초기화 (기본 공개 게이트웨이 노드 자동 연결)
    shield = PCAMShockShield()

    # 2. 가상의 연속 3틱 호가창 시뮬레이션 (평온 -> 급격한 호가 붕괴)
    scenarios = [
        {"name": "1. 평온한 시장 (Normal Liquid)", "bids": [[68000, 10.0]], "asks": [[68001, 10.2]]},
        {"name": "2. 매수벽 붕괴 조짐 (Imbalance Stress)", "bids": [[67995, 2.0]], "asks": [[68001, 25.0]]},
        {"name": "3. 거대 매도 폭탄 스윕 (Toxic Sweep Shock)", "bids": [[67970, 0.5]], "asks": [[68005, 80.0]]}
    ]

    for step in scenarios:
        print(f"\n▶ 시나리오: {step['name']}")
        mock_book = {"bids": step["bids"], "asks": step["asks"]}
        
        t0 = time.perf_counter()
        sig = shield.evaluate_ccxt(mock_book)
        elapsed_client_ms = (time.perf_counter() - t0) * 1000.0

        print(f" * 하드웨어 감쇠비 (Zeta) : {sig.zeta:.4f}")
        print(f" * 15µs 실리콘 반사 지연  : {sig.hardware_reflex_ms:.4f} ms")
        print(f" * 트레이딩 전략 액션     : [{sig.action}]")
        print(f" * 슬리피지 방어 트리거   : {sig.should_cancel} (Quote Pull)")
        print(f" * SEAL-CORE 하드웨어 봉인: {sig.hardware_seal_id[:35]}...")

        if sig.should_cancel:
            print(" 🚨 [ALERT] 거대 유동성 증발 감지! 기존 지정가 주문 전량 취소 -> 슬리피지 0원 방어 완료!")
        else:
            print(" 🟢 [SAFE] 정상 감쇠 구간. 유동성 공급(Maker) 주문 안전 유지.")

        time.sleep(0.5)

    print("\n" + "=" * 75)
    print("✔ CCXT Shield Attestation Complete.")
    print("=" * 75)

if __name__ == "__main__":
    main()
