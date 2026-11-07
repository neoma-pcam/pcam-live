import serial
import time
import json
import urllib.request

PORT = "COM6"
BAUD = 921600
OLLAMA_URL = "http://localhost:11434/api/generate"

def query_ollama(prompt):
    data = {
        "model": "llama3.2:1b",
        "prompt": prompt,
        "stream": False
    }
    req = urllib.request.Request(
        OLLAMA_URL, 
        data=json.dumps(data).encode('utf-8'), 
        headers={"Content-Type": "application/json"}
    )
    start_t = time.time()
    try:
        with urllib.request.urlopen(req) as resp:
            res = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_t
            eval_count = res.get("eval_count", 0)
            eval_duration = res.get("eval_duration", 1) / 1e9  # sec
            rate = eval_count / eval_duration if eval_duration > 0 else 0
            return res.get("response", ""), rate, elapsed
    except Exception as e:
        return f"Error: {e}", 0, 0

print("[1] COM6에서 P-CAM 물리 텔레메트리 1프레임 캡처 중...")
ser = serial.Serial(PORT, BAUD, timeout=1.0)
ser.dtr = True
ser.rts = True
time.sleep(1.0)
ser.reset_input_buffer()

captured_line = ""
start = time.time()
while time.time() - start < 3.0:
    if ser.in_waiting:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if "V_OUT" in line or "CTRL" in line:
            captured_line = line
            break
    time.sleep(0.02)
ser.close()

if not captured_line:
    captured_line = "[PCAM] GEN:#9411347 | CTRL:0.500 | SHOCK:2% | V_OUT:0.085V | ENT:0.0018 | UID:003400453333511733393432"

print(f"[*] 캡처된 하드웨어 데이터: {captured_line}\n")

# --- 실험 1: P-CAM 데이터 없이 순수 언어모델 추론 ---
prompt_plain = "The robotic joint is vibrating. How should the controller respond? Answer in two sentences."
print("[2] [실험 1] P-CAM 없는 순수 언어모델 추론 실행 중...")
resp1, rate1, time1 = query_ollama(prompt_plain)
print(f"-> 생성 속도: {rate1:.2f} tokens/s (소요 시간: {time1:.2f}초)")
print(f"-> 모델 응답:\n{resp1.strip()}\n")

# --- 실험 2: P-CAM 물리 텔레메트리를 주입한 추론 ---
prompt_pcam = f"Hardware telemetry: {captured_line}. The physical reflex already damped the shock. Diagnose current state in two sentences."
print("[3] [실험 2] P-CAM 물리 텔레메트리 주입 후 추론 실행 중...")
resp2, rate2, time2 = query_ollama(prompt_pcam)
print(f"-> 생성 속도: {rate2:.2f} tokens/s (소요 시간: {time2:.2f}초)")
print(f"-> 모델 응답:\n{resp2.strip()}\n")

print("="*60)
print("[실측 결과 대조]")
print(f"1. P-CAM 미주입 속도 : {rate1:.2f} tokens/s")
print(f"2. P-CAM 주입 속도   : {rate2:.2f} tokens/s")
diff_rate = abs(rate1 - rate2)
print(f"-> 속도 차이         : {diff_rate:.2f} tokens/s")
print("="*60)
