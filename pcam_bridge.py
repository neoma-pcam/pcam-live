import serial
import time
from fastapi import FastAPI, HTTPException
import uvicorn

app = FastAPI(title="P-CAM 002 Local Accelerator")

# COM6 연결
try:
    ser = serial.Serial("COM6", 115200, timeout=1.0)
except Exception as e:
    ser = None
    print(f"[Warning] COM6 포트 연결 대기 중: {e}")

def parse_pcam_output(raw_str: str) -> dict:
    # "NT:0.0010 | MODE:1" 등의 문자열을 딕셔너리로 구조화
    data = {"raw": raw_str}
    try:
        parts = [p.strip() for p in raw_str.split("|")]
        for part in parts:
            if ":" in part:
                k, v = part.split(":", 1)
                data[k.strip()] = v.strip()
    except Exception:
        pass
    return data

@app.api_route("/health", methods=["GET", "POST", "HEAD"])
def health():
    return {
        "status": "online" if ser and ser.is_open else "port_closed",
        "port": "COM6",
        "role": "P-CAM 002 Accelerator"
    }

@app.post("/accelerate")
def accelerate(payload: dict = {}):
    if not ser or not ser.is_open:
        raise HTTPException(status_code=500, detail="COM6 포트가 연결되어 있지 않습니다.")
    
    try:
        # P-CAM 002로 트리거 명령 전송
        cmd = payload.get("command", "PING")
        ser.reset_input_buffer()
        ser.write(f"{cmd}\n".encode("utf-8"))
        
        # 002 엣지 응답 수신
        line = ser.readline().decode("utf-8", errors="ignore").strip()
        if not line:
            raise HTTPException(status_code=504, detail="002 STM 응답 시간 초과")
            
        parsed = parse_pcam_output(line)
        return {
            "status": "success",
            "telemetry": parsed
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8002)

