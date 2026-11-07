import os
import sys
import time
import subprocess
import requests
from google import genai
from google.genai import types

# 1. API 키 불러오기 (파일 또는 환경변수)
KEY_FILE = r"C:\Users\shs15\gemini_key.txt"
api_key = os.environ.get("GEMINI_API_KEY")

if not api_key and os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()

if not api_key:
    raise ValueError("GEMINI_API_KEY를 찾을 수 없습니다. gemini_key.txt 파일에 키를 입력해주세요.")

client = genai.Client(api_key=api_key)

# 2. 8002번 가속기 브릿지 동작 확인 및 자동 실행
def ensure_bridge_running():
    try:
        requests.get("http://127.0.0.1:8002/health", timeout=1.0)
    except Exception:
        print("[시스템] P-CAM 002 가속기 브릿지 서버(8002) 자동 시작 중...")
        subprocess.Popen(
            [sys.executable, "pcam_bridge.py"],
            cwd=r"C:\Users\shs15",
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        time.sleep(2)

ensure_bridge_running()

# 3. 로컬 P-CAM 002 가속기 도구 함수
def fetch_pcam_telemetry(command: str = "PING") -> dict:
    """
    P-CAM 002 하드웨어 가속기(COM27)로부터 실시간 물리 센싱 데이터(전압, 엔트로피, 제어 모드)를 즉각 수신합니다.
    """
    try:
        res = requests.post("http://127.0.0.1:8002/accelerate", json={"command": command}, timeout=2.0)
        return res.json()
    except Exception as e:
        return {"error": f"가속기 통신 실패: {str(e)}"}

# 4. 제미나이 채팅 세션 초기화
chat = client.chats.create(
    model="gemini-3.1-pro-preview",
    config=types.GenerateContentConfig(
        system_instruction=(
            "당신은 피지컬 AI '네오마(Neoma)'의 중앙 지능입니다. "
            "P-CAM(Predictive Control Adaptive Material)의 핵심은 현장을 실시간으로 센싱하여 물질의 어려움을 예측·조절하는 것입니다. "
            "물리적 상태, 전압, 엔트로피 진단이나 현장 제어가 필요할 때 반드시 fetch_pcam_telemetry 도구를 호출하여 "
            "P-CAM 002 가속기의 실시간 물리 신호를 기반으로 진단하고 명확하게 답변하십시오."
        ),
        tools=[fetch_pcam_telemetry],
        temperature=0.2
    )
)

print("=" * 60)
print("네오마(Neoma) 피지컬 AI 콘솔 가동 완료 (종료: 'exit')")
print("=" * 60)

while True:
    try:
        user_input = input("\n[질의 입력] > ").strip()
        if not user_input:
            continue
        if user_input.lower() in ["exit", "quit", "q"]:
            print("네오마 콘솔을 종료합니다.")
            break

        print("[네오마 인지 및 가속기 연산 중...]")
        response = chat.send_message(user_input)
        print(f"\n[네오마 진단]:\n{response.text}")

    except KeyboardInterrupt:
        print("\n종료합니다.")
        break
    except Exception as e:
        print(f"\n[에러 발생]: {e}")


