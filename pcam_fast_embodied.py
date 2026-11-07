import json
import time
import urllib.request

OLLAMA_URL = "http://localhost:11434/api/generate"

# Q12 고정소수점 상태 레지스터
# VOUT=348 (0.085V), CTRL=2048 (0.500 평형), SHOCK=3482 (85%), ENT=141
prompt_embodied = """[SYSTEM: PCAM_CORE_EMBODIED]
REGISTER_Q12: VOUT=348 CTRL=2048 SHOCK=3482 ENT=141
RULE: Do not explain. Output ONLY one state code: [CRITICAL | DAMPED_STABLE | RUNAWAY].
STATE:"""

data = {
    "model": "llama3.2:1b",
    "prompt": prompt_embodied,
    "stream": False,
    "options": {
        "temperature": 0.0,
        "num_predict": 5  # 사설 차단, 최대 5토큰 이내 종결
    }
}

req = urllib.request.Request(
    OLLAMA_URL,
    data=json.dumps(data).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

print("[*] 1-토큰 체화 매핑 실행 중...")
t0 = time.time()
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
latency = (time.time() - t0) * 1000  # ms 단위

print("="*50)
print(f"-> 소요 시간(Latency) : {latency:.2f} ms")
print(f"-> 생성 토큰 수       : {res.get('eval_count', 0)} tokens")
print(f"-> 모델 즉시 판단 결과: {res.get('response', '').strip()}")
print("="*50)
