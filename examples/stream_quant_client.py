import asyncio
import json
import websockets

async def pcam_stream_demo():
    # 로컬 테스트: ws://127.0.0.1:8000/v1/quant/stream
    # 운영 환경: wss://api.neoma-pcam.com/v1/quant/stream
    uri = "ws://127.0.0.1:8000/v1/quant/stream"
    print(f"[*] Connecting to P-CAM Real-time Stream: {uri}")
    
    async with websockets.connect(uri) as ws:
        print("[+] Connection established. Streaming order book disturbance ticks...\n")
        
        ticks = [
            {"flux_potential_v": 0.082, "gradient_velocity": 450.0, "gradient_acceleration": 15000.0, "active_strain": 1.02},
            {"flux_potential_v": 0.088, "gradient_velocity": 780.0, "gradient_acceleration": 28000.0, "active_strain": 1.25},
            {"flux_potential_v": 0.091, "gradient_velocity": 1100.0, "gradient_acceleration": 42000.0, "active_strain": 1.48},
        ]
        
        for idx, tick in enumerate(ticks, 1):
            await ws.send(json.dumps(tick))
            res = json.loads(await ws.recv())
            print(f"Tick #{idx:02d} | Velocity: {tick['gradient_velocity']} | Zeta: {res['zeta']} | Reflex: {res['hardware_reflex_ms']}ms")
            print(f"         Hardware Seal: {res['hardware_seal_id']}")
            print(f"         Cognitive    : {res['phi_embodied_cognition'][:80]}...\n")

if __name__ == "__main__":
    asyncio.run(pcam_stream_demo())
