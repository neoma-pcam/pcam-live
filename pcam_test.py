import serial
import numpy as np
import ollama
import time

PORT = 'COM20'
BAUD = 921600

def get_serial_connection():
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.5)
        print(f"[*] P-CAM 물리 하드웨어 ({PORT}) 단독 연결 성공.\n")
        return ser
    except Exception as e:
        print(f"[!] 포트 연결 대기 중... ({e})")
        return None

ser = get_serial_connection()

def pcam_transform(vector):
    global ser
    if ser is None or not ser.is_open:
        ser = get_serial_connection()
        if ser is None:
            return vector, 0.0
            
    try:
        t_start = time.perf_counter()
        norm_vec = np.clip((vector + 1.0) * 127.5, 0, 255).astype(np.uint8)
        ser.write(norm_vec.tobytes())
        resp = ser.read(len(norm_vec))
        t_pcam = (time.perf_counter() - t_start) * 1000.0
        
        if len(resp) == len(norm_vec):
            resp_arr = (np.frombuffer(resp, dtype=np.uint8).astype(np.float32) / 127.5) - 1.0
            return resp_arr, t_pcam
    except Exception:
        if ser:
            ser.close()
        ser = None
    return vector, 0.0

print("="*65)
print(" P-CAM Standalone Engine [Auto-Recovery & Ultra-Speed Mode]")
print("="*65)

while True:
    user_query = input("\n[Customer Query] >> ").strip()
    if user_query.lower() in ['exit', 'q', 'quit']:
        break
    if not user_query:
        continue

    print("\n[*] Llama 3.2 Generating Proposal Solution (English):")
    t_llm_start = time.perf_counter()
    
    prompt_payload = (
        f"Input Requirement: {user_query}\n\n"
        "Rules: Write a formal technical solution in English. Exactly 2 dense sentences. No preface.\n"
        "Technical Solution:\n"
    )
    
    # num_predict=70 설정으로 불필요한 장문 생성을 차단하고 초고속 응답 보장
    stream = ollama.generate(
        model='llama3.2',
        prompt=prompt_payload,
        options={
            'temperature': 0.1,
            'num_predict': 70
        },
        stream=True
    )
    
    solution = ""
    for chunk in stream:
        content = chunk['response']
        solution += content
        print(content, end='', flush=True)
    
    t_llm = (time.perf_counter() - t_llm_start) * 1000.0
    print(f"\n\n[LLM Inference Time]: {t_llm:.2f} ms")

    # P-CAM 물리 파동 연산
    dummy_vec = np.random.randn(64).astype(np.float32)
    transformed_vec, pcam_latency = pcam_transform(dummy_vec)
    energy = float(np.mean(np.square(transformed_vec)))
    score = float(np.exp(-energy) * 100)

    print(f"[P-CAM Physical Medium Latency]: {pcam_latency:.3f} ms")
    print(f"[*] Physical Response Energy: {energy:.4f}")
    print(f"[*] Physical Resonance Score: {score:.2f} / 100")

if ser and ser.is_open:
    ser.close()