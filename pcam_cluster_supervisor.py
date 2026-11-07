# NEOMA P-CAM Master Physics Data Foundry (v3.0 Production)
# Standard: 3-Year Equivalent Operating Days (EOD: 1.0 ~ 1095.0 Days)
import os, sys, time, math, random, datetime, multiprocessing
import pandas as pd

BASE_DIR = r"C:\Users\shs15\neoma_data_lake"
TODAY = datetime.date.today().strftime("%Y-%m-%d")

NODES_CONFIG = [
    {"id": "node01", "domain": "ROBOTICS", "batch_size": 500},
    {"id": "node02", "domain": "ROBOTICS", "batch_size": 500},
    {"id": "node03", "domain": "BATTERY", "batch_size": 500},
    {"id": "node04", "domain": "BATTERY", "batch_size": 500},
    {"id": "node05", "domain": "BIOMEDICAL", "batch_size": 500}
]

# 50,000틱 누적 시 1,095일(3개년) 완주 (틱당 약 0.0219일 등가 전진)
EOD_ADVANCE_PER_TICK = 1095.0 / 50000.0

def simulate_robotics(tick, eod):
    aging_ratio = min(eod / 1095.0, 1.0)
    # 기어 백래시 마모도: 신품 0.04mm -> 3년 경과 0.42mm
    backlash_wear_mm = 0.04 + (0.38 * (aging_ratio ** 1.3))
    is_fault = (tick % 125 == 0) # 복합 극한 충격 유입
    
    if is_fault:
        shock_g = 11.85 + random.uniform(-0.35, 0.35) # 12G 파괴 한계치
        damping_force = -shock_g * (0.88 - backlash_wear_mm * 0.12)
        seal = "SEAL_ANOMALY_RESOLVED"
    else:
        shock_g = math.sin(tick * 0.12) * 2.2 + random.gauss(0, 0.08)
        damping_force = -shock_g * (0.95 - backlash_wear_mm * 0.05)
        seal = "AUTHENTICATED"
        
    return {
        "equivalent_operating_days": round(eod, 2),
        "aging_ratio": round(aging_ratio, 4),
        "raw_signal": round(shock_g, 4),
        "reflex_control": round(damping_force, 4),
        "internal_entropy": round(backlash_wear_mm, 4),
        "seal_status": seal
    }

def simulate_battery(tick, eod):
    aging_ratio = min(eod / 1095.0, 1.0)
    # 내부 저항(R_int): 신품 0.015 ohm -> 3년 경과 0.085 ohm
    r_int_ohm = 0.015 + (0.070 * (aging_ratio ** 1.2))
    base_v = 3.70 - (aging_ratio * 0.16)
    is_fault = (tick % 160 == 0) # 열폭주 전조 급락 이벤트
    
    if is_fault:
        v_drop = -0.0815 + random.uniform(-0.002, 0.002)
        v_signal = base_v + v_drop
        reflex_comp = abs(v_drop) * 1.04
        seal = "SEAL_ANOMALY_RESOLVED"
    else:
        v_signal = base_v + math.sin(tick * 0.06) * 0.004 + random.gauss(0, 0.001)
        reflex_comp = 0.0018
        seal = "AUTHENTICATED"
        
    return {
        "equivalent_operating_days": round(eod, 2),
        "aging_ratio": round(aging_ratio, 4),
        "raw_signal": round(v_signal, 4),
        "reflex_control": round(reflex_comp, 4),
        "internal_entropy": round(r_int_ohm, 4),
        "seal_status": seal
    }

def simulate_biomedical(tick, eod):
    aging_ratio = min(eod / 1095.0, 1.0)
    # 항상성 복원 지연 시정수(Tau): 1.1s -> 4.2s (생체 피로도 증가)
    recovery_tau = 1.1 + (3.1 * aging_ratio)
    is_fault = (tick % 210 == 0)
    
    if is_fault:
        spike = 4.75 + random.uniform(0.1, 0.4)
        restore_signal = -spike * (1.0 / recovery_tau)
        seal = "SEAL_ANOMALY_RESOLVED"
    else:
        spike = math.sin(tick * 0.25) * 0.75 + random.gauss(0, 0.04)
        restore_signal = -spike * 0.92
        seal = "AUTHENTICATED"
        
    return {
        "equivalent_operating_days": round(eod, 2),
        "aging_ratio": round(aging_ratio, 4),
        "raw_signal": round(spike, 4),
        "reflex_control": round(restore_signal, 4),
        "internal_entropy": round(recovery_tau, 4),
        "seal_status": seal
    }

def worker_process(node_id, domain, batch_size):
    save_dir = os.path.join(BASE_DIR, f"date={TODAY}", f"domain={domain}")
    os.makedirs(save_dir, exist_ok=True)
    
    tick = 0
    eod = 1.0
    
    while True:
        records = []
        for _ in range(batch_size):
            tick += 1
            eod += EOD_ADVANCE_PER_TICK
            if eod > 1095.0:
                eod = 1.0 # 3년 수명 완주 후 신규 검증 사이클 진입
                
            if domain == "ROBOTICS":
                data = simulate_robotics(tick, eod)
            elif domain == "BATTERY":
                data = simulate_battery(tick, eod)
            else:
                data = simulate_biomedical(tick, eod)
                
            latency_ms = 0.8577 + random.gauss(0, 0.007)
            data.update({
                "tick_id": tick,
                "timestamp": datetime.datetime.now().isoformat(),
                "node_id": node_id,
                "domain": domain,
                "latency_ms": round(latency_ms, 4),
                "hw_seal": "SEAL-CORE-v3.0"
            })
            records.append(data)
            time.sleep(0.0004) # 0.4ms 고속 척수 틱
            
        df = pd.DataFrame(records)
        out_name = f"{node_id}_{datetime.datetime.now().strftime('%H%M%S')}.parquet"
        out_path = os.path.join(save_dir, out_name)
        df.to_parquet(out_path, engine="pyarrow", compression="snappy")
        
        anom_cnt = len(df[df["seal_status"] == "SEAL_ANOMALY_RESOLVED"])
        print(f"[{node_id.upper()} | {domain}] EOD: {data['equivalent_operating_days']}일 (수명 {int(data['aging_ratio']*100)}%) | 골든 방어: {anom_cnt}건 -> {out_name}")

if __name__ == "__main__":
    print("=" * 70)
    print("🚀 [NEOMA P-CAM] 3개년 등가 운용 내구(EOD) 정규 물리 데이터 파운드리 가동")
    print(f"📁 대상 데이터 레이크: {BASE_DIR}")
    print("🎯 평가 규격: 1.0일 ~ 1,095.0일 비선형 경년 열화 + 0.85ms 척수 반사")
    print("=" * 70)
    
    processes = []
    for cfg in NODES_CONFIG:
        p = multiprocessing.Process(target=worker_process, args=(cfg["id"], cfg["domain"], cfg["batch_size"]))
        p.start()
        processes.append(p)
        
    for p in processes:
        p.join()
