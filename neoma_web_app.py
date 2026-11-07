import os
import sys
import time
import sqlite3
import datetime
import subprocess
import requests
import streamlit as st
from google import genai
from google.genai import types

# --- 1. 환경변수 및 실행 모델 감지 ---
ACTIVE_MODEL = os.environ.get("NEOMA_MODEL", "gemini-3.1-pro-preview")
MODEL_ALIAS = "Pro (심층 추론 / gemini-3.1-pro-preview)" if "pro" in ACTIVE_MODEL.lower() else "Flash (고속·절약 / gemini-2.5-flash)"

DB_PATH = r"C:\Users\shs15\neoma_memory.db"
KEY_FILE = r"C:\Users\shs15\gemini_key.txt"

def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            role TEXT,
            content TEXT
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS sensor_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp TEXT,
            voltage TEXT,
            entropy TEXT,
            mode TEXT,
            raw TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# 8002번 브릿지 자동 실행 확인
def ensure_bridge_running():
    try:
        requests.get("http://127.0.0.1:8002/health", timeout=0.5)
    except Exception:
        subprocess.Popen(
            [sys.executable, "pcam_bridge.py"],
            cwd=r"C:\Users\shs15",
            creationflags=subprocess.CREATE_NEW_CONSOLE
        )
        time.sleep(2)

ensure_bridge_running()

# API 키 로드
api_key = os.environ.get("GEMINI_API_KEY")
if not api_key and os.path.exists(KEY_FILE):
    with open(KEY_FILE, "r", encoding="utf-8") as f:
        api_key = f.read().strip()

client = genai.Client(api_key=api_key)

# --- 2. 로컬 가속기 도구 및 DB 기록 함수 ---
def fetch_pcam_telemetry(command: str = "PING") -> dict:
    """
    P-CAM 003 하드웨어 가속기(COM6)로부터 실시간 물리 센싱 데이터를 수신하고 로컬 DB에 자동 저장합니다.
    """
    try:
        res = requests.post("http://127.0.0.1:8002/accelerate", json={"command": command}, timeout=2.0)
        data = res.json()
        if "telemetry" in data:
            t = data["telemetry"]
            raw_text = t.get("raw", "")
            volt = raw_text.split("|")[0].strip() if "|" in raw_text else ""
            ent = t.get("ENT", "")
            mode = t.get("MODE", "")
            now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("INSERT INTO sensor_logs (timestamp, voltage, entropy, mode, raw) VALUES (?, ?, ?, ?, ?)",
                      (now, volt, ent, mode, raw_text))
            conn.commit()
            conn.close()
        return data
    except Exception as e:
        return {"error": f"가속기 통신 실패: {str(e)}"}

# --- 3. Streamlit 웹 인터페이스 ---
st.set_page_config(page_title="Neoma Physical AI", page_icon="⚡", layout="wide")

with st.sidebar:
    st.title("⚡ 네오마 제어반")
    st.caption("P-CAM 003 (COM6) 로컬 전용 가속기")
    st.success(f"🧠 활성 두뇌: **{MODEL_ALIAS}**")

    if st.button("현재 센서 즉시 측정 및 기록"):
        sensor_res = fetch_pcam_telemetry("PING")
        st.write(sensor_res)

    st.divider()
    st.subheader("📊 최근 센싱 기록 (로컬 DB)")
    conn = sqlite3.connect(DB_PATH)
    recent_sensors = conn.execute("SELECT timestamp, voltage, entropy, mode FROM sensor_logs ORDER BY id DESC LIMIT 5").fetchall()
    conn.close()
    if recent_sensors:
        for row in recent_sensors:
            st.text(f"[{row[0][11:]}] {row[1]} | ENT:{row[2]} | M:{row[3]}")
    else:
        st.info("기록된 센서 데이터가 없습니다.")

    st.divider()
    if st.button("대화 기록 초기화"):
        conn = sqlite3.connect(DB_PATH)
        conn.execute("DELETE FROM chats")
        conn.commit()
        conn.close()
        st.session_state.messages = []
        st.rerun()

st.title("🌐 네오마(Neoma) 피지컬 AI 콘솔")
st.caption(f"엔진 모드: **{MODEL_ALIAS}** | P-CAM 003 물리 직결")

if "messages" not in st.session_state:
    st.session_state.messages = []
    conn = sqlite3.connect(DB_PATH)
    saved_chats = conn.execute("SELECT role, content FROM chats ORDER BY id ASC").fetchall()
    conn.close()
    for role, content in saved_chats:
        st.session_state.messages.append({"role": role, "content": content})

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if user_prompt := st.chat_input("현장 센싱 또는 제어 명령을 입력하세요..."):
    st.chat_message("user").markdown(user_prompt)
    st.session_state.messages.append({"role": "user", "content": user_prompt})

    now = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = sqlite3.connect(DB_PATH)
    conn.execute("INSERT INTO chats (timestamp, role, content) VALUES (?, ?, ?)", (now, "user", user_prompt))
    conn.commit()
    conn.close()

    with st.chat_message("assistant"):
        with st.spinner(f"[{MODEL_ALIAS}] 인지 추론 및 가속기 연동 중..."):
            try:
                history_context = "\n".join([f"{m['role']}: {m['content']}" for m in st.session_state.messages[-6:-1]])
                full_prompt = f"과거 대화 맥락:\n{history_context}\n\n사용자 입력: {user_prompt}" if history_context else user_prompt

                response = client.models.generate_content(
                    model=ACTIVE_MODEL,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(
                        system_instruction=(
                            "당신은 피지컬 AI '네오마(Neoma)'의 중앙 지능입니다. "
                            "P-CAM(Predictive Control Adaptive Material)의 핵심은 현장을 실시간으로 센싱하여 물질의 어려움을 예측·조절하는 것입니다. "
                            "물리적 상태, 전압, 엔트로피 진단이나 현장 제어가 필요할 때 반드시 fetch_pcam_telemetry 도구를 호출하여 "
                            "P-CAM 003 가속기의 실시간 물리 신호를 기반으로 진단하십시오."
                        ),
                        tools=[fetch_pcam_telemetry],
                        temperature=0.2
                    )
                )
                answer_text = response.text
                st.markdown(answer_text)

                st.session_state.messages.append({"role": "assistant", "content": answer_text})
                conn = sqlite3.connect(DB_PATH)
                conn.execute("INSERT INTO chats (timestamp, role, content) VALUES (?, ?, ?)", (now, "assistant", answer_text))
                conn.commit()
                conn.close()

            except Exception as e:
                st.error(f"오류가 발생했습니다: {e}")

