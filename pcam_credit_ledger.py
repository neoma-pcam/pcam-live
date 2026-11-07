import sqlite3
import time
from typing import Dict, Any

DB_PATH = "pcam_silent_ledger.db"

def init_ledger():
    """원장 DB 초기화 및 지갑 매핑 스키마 자동 업그레이드"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    cursor.execute("PRAGMA journal_mode=WAL;")
    
    # 1. 고객별/운영자별 잔고 및 온체인 지갑 주소 필드
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS accounts (
            client_id TEXT PRIMARY KEY,
            customer_credits REAL DEFAULT 0.0,
            owner_equity_credits REAL DEFAULT 0.0,
            burned_credits REAL DEFAULT 0.0,
            total_cash_usd REAL DEFAULT 0.0,
            paid_calls_count INTEGER DEFAULT 0,
            wallet_address TEXT DEFAULT NULL
        )
    """)
    
    # 기존 DB 테이블 호환성 보장 (wallet_address 컬럼 없을 시 자동 추가)
    try:
        cursor.execute("ALTER TABLE accounts ADD COLUMN wallet_address TEXT DEFAULT NULL;")
    except sqlite3.OperationalError:
        pass  # 이미 컬럼이 존재하면 통과

    # 2. 거래 및 감사 증명 로그
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS audit_trail (
            tx_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            client_id TEXT,
            source TEXT,
            order_id TEXT,
            physical_gen INTEGER,
            seal_id TEXT,
            cash_amount_usd REAL,
            minted_customer REAL,
            minted_owner REAL
        )
    """)
    
    # 3. 5% 할인 환급 및 소각 영수증 장부
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS burn_receipts (
            burn_id INTEGER PRIMARY KEY AUTOINCREMENT,
            timestamp REAL,
            client_id TEXT,
            burned_amount REAL,
            discount_usd_applied REAL
        )
    """)
    conn.commit()
    conn.close()

def register_wallet(client_id: str, wallet_address: str) -> Dict[str, Any]:
    """
    온체인 토큰 마이그레이션용 Web3 지갑 주소 매핑 등록 (EVM 0x... 또는 Solana)
    """
    clean_addr = wallet_address.strip()
    if not clean_addr or len(clean_addr) < 26:
        return {"success": False, "reason": "Invalid wallet address format (Must be valid EVM or Solana address)"}

    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (client_id, wallet_address)
            VALUES (?, ?)
            ON CONFLICT(client_id) DO UPDATE SET
                wallet_address = ?
        """, (client_id, clean_addr, clean_addr))
        conn.commit()
        conn.close()
        return {
            "success": True,
            "client_id": client_id,
            "wallet_address": clean_addr,
            "status": "WALLET_BOUND_SUCCESSFULLY"
        }
    except Exception as e:
        return {"success": False, "reason": str(e)}

def record_lemonsqueezy_cash(client_id: str, cash_amount_usd: float, order_id: str):
    """실결제 시 100% 현금 담보 크레딧 발행 ($1 = 고객 1.0 / 주인 0.1)"""
    if cash_amount_usd <= 0:
        return

    customer_mint = cash_amount_usd * 1.0
    owner_mint = cash_amount_usd * 0.1
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO accounts (client_id, customer_credits, owner_equity_credits, total_cash_usd)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(client_id) DO UPDATE SET
                customer_credits = customer_credits + ?,
                owner_equity_credits = owner_equity_credits + ?,
                total_cash_usd = total_cash_usd + ?
        """, (client_id, customer_mint, owner_mint, cash_amount_usd,
              customer_mint, owner_mint, cash_amount_usd))
        
        cursor.execute("""
            INSERT INTO audit_trail (timestamp, client_id, source, order_id, physical_gen, seal_id, cash_amount_usd, minted_customer, minted_owner)
            VALUES (?, ?, 'LEMON_SQUEEZY', ?, 0, 'LEMON_CASH_CONFIRMED', ?, ?, ?)
        """, (time.time(), client_id, str(order_id), cash_amount_usd, customer_mint, owner_mint))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LEDGER_ERROR] Lemon Squeezy minting failed: {e}")

def record_rapidapi_call(client_id: str, subscription_plan: str, physical_gen: int, seal_id: str, unit_price_usd: float = 1.0):
    """RapidAPI 유료 구독자만 크레딧 발행"""
    plan = (subscription_plan or "BASIC").upper()
    is_paid = plan not in ["BASIC", "FREE", "TEST", "ANONYMOUS"]
    
    customer_mint = (unit_price_usd * 1.0) if is_paid else 0.0
    owner_mint = (unit_price_usd * 0.1) if is_paid else 0.0
    cash_inflow = unit_price_usd if is_paid else 0.0
    
    try:
        conn = sqlite3.connect(DB_PATH, timeout=5.0)
        cursor = conn.cursor()
        
        if is_paid:
            cursor.execute("""
                INSERT INTO accounts (client_id, customer_credits, owner_equity_credits, total_cash_usd, paid_calls_count)
                VALUES (?, ?, ?, ?, 1)
                ON CONFLICT(client_id) DO UPDATE SET
                    customer_credits = customer_credits + ?,
                    owner_equity_credits = owner_equity_credits + ?,
                    total_cash_usd = total_cash_usd + ?,
                    paid_calls_count = paid_calls_count + 1
            """, (client_id, customer_mint, owner_mint, cash_inflow,
                  customer_mint, owner_mint, cash_inflow))
        
        cursor.execute("""
            INSERT INTO audit_trail (timestamp, client_id, source, order_id, physical_gen, seal_id, cash_amount_usd, minted_customer, minted_owner)
            VALUES (?, ?, ?, 'RAPID_CALL', ?, ?, ?, ?, ?)
        """, (time.time(), client_id, f"RAPID_{plan}", physical_gen, seal_id, cash_inflow, customer_mint, owner_mint))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[LEDGER_ERROR] RapidAPI call logging failed: {e}")

def redeem_and_burn_credits(client_id: str, request_credits: float) -> Dict[str, Any]:
    """5% 할인 청구 시 소각 (1코인 = $0.05 환급 가치)"""
    conn = sqlite3.connect(DB_PATH, timeout=10.0)
    cursor = conn.cursor()
    
    cursor.execute("SELECT customer_credits FROM accounts WHERE client_id = ?", (client_id,))
    row = cursor.fetchone()
    
    if not row or row[0] < request_credits:
        conn.close()
        return {"success": False, "reason": "Insufficient customer credits"}
    
    discount_usd = request_credits * 0.05  # 5% 할인 가치
    
    cursor.execute("""
        UPDATE accounts
        SET customer_credits = customer_credits - ?,
            burned_credits = burned_credits + ?
        WHERE client_id = ?
    """, (request_credits, request_credits, client_id))
    
    cursor.execute("""
        INSERT INTO burn_receipts (timestamp, client_id, burned_amount, discount_usd_applied)
        VALUES (?, ?, ?, ?)
    """, (time.time(), client_id, request_credits, discount_usd))
    
    conn.commit()
    conn.close()
    
    return {
        "success": True,
        "burned_credits": request_credits,
        "discount_usd_applied": discount_usd,
        "burn_status": "PERMANENTLY_BURNED"
    }

def get_account_balance(client_id: str) -> Dict[str, Any]:
    """잔고, 지갑 주소, 누적 현금 및 5% 할인 가능액 조회"""
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT customer_credits, owner_equity_credits, burned_credits, total_cash_usd, wallet_address 
        FROM accounts WHERE client_id = ?
    """, (client_id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        return {
            "client_id": client_id,
            "customer_credits": 0.0,
            "owner_equity_credits": 0.0,
            "burned_credits": 0.0,
            "wallet_address": None,
            "discount_value_usd": 0.0
        }
    return {
        "client_id": client_id,
        "customer_credits": row[0],
        "owner_equity_credits": row[1],
        "burned_credits": row[2],
        "total_cash_usd": row[3],
        "wallet_address": row[4],  # 등록된 온체인 지갑 주소
        "discount_value_usd": row[0] * 0.05
    }

init_ledger()