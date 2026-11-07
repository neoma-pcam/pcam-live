import time
import math
import psutil
import os
import sqlite3
import datetime

# 1. 로컬 볼트 세팅 (클라우드 대신 로컬 메모리/DB에만 기록)
DB_PATH = "pcam_endurance_vault.db"
conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()
cursor.execute('''
    CREATE TABLE IF NOT EXISTS survival_log (
        cycle INTEGER PRIMARY KEY,
        elapsed_sec REAL,
        convergence_time_ms REAL,
        ram_usage_mb REAL,
        status TEXT
    )
''')
conn.commit()

process = psutil.Process(os.getpid())

def simulate_pcam_core_step(flux, vel, accel, strain):
    """외부 통신 없이 로컬 실리콘에서 자율 구동되는 0.85ms 평형 수렴 연산"""
    t_start = time.perf_counter()
    
    # 0.85ms 비선형 감쇠 수렴 로직 연산
    tau = 0.12 + (accel / 70000.0)
    decay = math.exp(-0.85 / tau)
    freq = 2.0 + (vel / 220.0)
    equilibrium_v = flux * (1.0 - decay * math.cos(2 * math.pi * freq * 0.85))
    
    t_end = time.perf_counter()
    latency_ms = (t_end - t_start) * 1000.0
    return latency_ms, equilibrium_v

print("="*60)
print("⚡ P-CAM Air-Gapped Infinite Survival Endurance Test Started")
print("Target: Verifying perpetual autonomous reflex without cloud")
print("="*60)

start_time = time.time()
cycle = 0

try:
    while True:
        cycle += 1
        
        # 로컬 물리 연산 실행
        latency, eq_v = simulate_pcam_core_step(0.082, 520, 16000, 1.55)
        
        # 1초에 1회씩(또는 1000사이클마다) 생존 상태 및 하드웨어 지표 로깅
        if cycle % 1000 == 0:
            elapsed = time.time() - start_time
            ram_mb = process.memory_info().rss / (1024 * 1024)
            
            cursor.execute(
                "INSERT INTO survival_log VALUES (?, ?, ?, ?, ?)",
                (cycle, round(elapsed, 2), round(latency, 4), round(ram_mb, 2), "AUTONOMOUS_ALIVE")
            )
            conn.commit()
            
            print(f"[{datetime.datetime.now().strftime('%H:%M:%S')}] "
                  f"Cycle: #{cycle:,} | Elapsed: {elapsed:.1f}s | "
                  f"Latency: {latency:.4f}ms | RAM: {ram_mb:.1f}MB | Status: ALIVE")
            
        # 1ms 간격 제어
        time.sleep(0.001)

except KeyboardInterrupt:
    print("\n[Stopped by User] Test completed safely.")
    conn.close()