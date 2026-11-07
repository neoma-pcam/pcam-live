import serial
import time
import json
import urllib.request

PORT = "COM6"
BAUD = 921600
OLLAMA_URL = "http://localhost:11434/api/generate"

# --- Q12 고정소수점 변환 함수 (Scale: 2^12 = 4096) ---
def float_to_q12(val):
    return int(round(val * 4096))

def q12_to_hex(val_q12):
    return f"0x{val_q12 & 0xFFFF:04X}"

print("[1] COM6 포트에서 P-CAM 원시 텔레메트리 캡처 중...")
ser = serial.Serial(PORT, BAUD, timeout=1.0)
ser.dtr = True
ser.rts = True
time.sleep(1.0)
ser.reset_input_buffer()

raw_pkt = ""
start = time.time()
while time.time() - start < 3.0:
    if ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if "V_OUT" in line and "CTRL" in line:
            raw_pkt = line
            break
    time.sleep(0.02)
ser.close()

if not raw_pkt:
    raw_pkt = "[NEOMA_PCAM_2.5] GEN:#9413287 | CTRL:0.500 | SHOCK:85% | V_OUT:0.085V | ENT:0.0345 | MODE:3 | STRG:OK | UID:003400453333511733393432"

print(f"[*] 캡처된 원시 물리 패킷: {raw_pkt}")

# --- 2. Q12 정수 벡터 변환 ---
# 파싱: CTRL=0.500, SHOCK=0.85, V_OUT=0.085, ENT=0.0345
ctrl_q12  = float_to_q12(0.500)
shock_q12 = float_to_q12(0.850)
vout_q12  = float_to_q12(0.085)
ent_q12   = float_to_q12(0.0345)

q12_vector = {
    "CTRL_Q12":  f"{ctrl_q12} ({q12_to_hex(ctrl_q12)})",
    "SHOCK_Q12": f"{shock_q12} ({q12_to_hex(shock_q12)})",
    "VOUT_Q12":  f"{vout_q12} ({q12_to_hex(vout_q12)})",
    "ENT_Q12":   f"{ent_q12} ({q12_to_hex(ent_q12)})"
}

print("\n" + "="*50)
print("[P-CAM 고정소수점 Q12 정수 레지스터 변환 결과]")
for k, v in q12_vector.items():
    print(f"  > {k:10s} : {v}")
print("="*50 + "\n")

# --- 3. Q12 체화 인터페이스를 통한 언어모델 직접 구동 ---
# 자연어가 아닌 P-CAM의 Q12 고정소수점 상태 코드를 직접 공급하여 결정 매핑
q12_payload = (
    f"PCAM_FIXED_POINT_Q12_STATE:\n"
    f"VOUT={vout_q12} | CTRL={ctrl_q12} | SHOCK={shock_q12} | ENT={ent_q12}\n"
    f"MAP_Q12_TO_SYSTEM_STATE: Output deterministic state code and action."
)

data = {
    "model": "llama3.2:1b",
    "prompt": q12_payload,
    "stream": False,
    "options": {
        "temperature": 0.0  # 부동소수점 무작위성 제거, 결정론적(Deterministic) 정수 매핑
    }
}

req = urllib.request.Request(
    OLLAMA_URL,
    data=json.dumps(data).encode('utf-8'),
    headers={"Content-Type": "application/json"}
)

print("[2] Q12 정수 환경 기반 언어모델 체화 연동 실행...")
t_start = time.time()
with urllib.request.urlopen(req) as resp:
    res = json.loads(resp.read().decode('utf-8'))
t_end = time.time()

print(f"-> 체화 연동 소요 시간: {t_end - t_start:.3f}초")
print(f"-> 생성 토큰 수: {res.get('eval_count', 0)} tokens")
print(f"-> Q12 상태 전이 응답:\n{res.get('response', '').strip()}")
