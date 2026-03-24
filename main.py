import socket
import time
import requests
import websocket
import json
import os
import sys
import traceback
from datetime import datetime, timedelta, timezone

# ==========================================
# HELPER: THE SYMBOL GUIDE
# ==========================================
def print_symbol_guide():
    print("=======================================================")
    print(" FULL SUPPORTED SYMBOLS REFERENCE GUIDE")
    print("=======================================================")
    
    print("\n--- FOREX, METALS & STANDARD CRYPTO PAIRS ---")
    print("USDJPY, USDCHF, EURUSD, GBPUSD, EURGBP, EURJPY, GBPJPY, USDCAD,")
    print("AUDUSD, EURCHF, USDPLN, EURPLN, USDMXN, EURMXN, CHFJPY, GBPCHF,")
    print("EURAUD, EURCAD, AUDCAD, AUDJPY, NZDUSD, AUDNZD, XAUUSD, XAGUSD,")
    print("CADJPY, USDTRY, USDHKD, USDSGD, USDCNH, EURTRY, NZDJPY, EURSEK,")
    print("GBPCAD, GBPAUD, AUDCHF, CADCHF, EURNZD, GBPNZD, NZDCAD, NZDCHF,")
    print("USDZAR, XPTUSD, XPDUSD, ZARJPY, XAUEUR, USDTHB, USDSEK, USDNOK,")
    print("USDHUF, USDDKK, SGDJPY, GBPZAR, EURZAR, XAGEUR, EURNOK, EURHUF,")
    print("EURDKK, NOKJPY, NOKSEK, USDRUB, EURRUB, TRYJPY, BTCUSD, BTCEUR,")
    print("BTCJPY, ETHUSD, LTCUSD, DSHUSD, ETCUSD, ETHEUR, ETHJPY, LTCEUR,")
    print("NEOETH, LTCBTC, ETHBTC, ETCBTC, DSHBTC, BTGBTC, NEOBTC, TRXETH,")
    print("BCHUSD, BCHBTC, BCHEUR, EOSUSD, EOSEUR, EOSBTC, BNBBTC")

    print("\n--- CFDs (INDICES & STOCKS) ---")
    print("AAPL (Apple)          AMZN (Amazon)         AUS200 (ASX200)")
    print("AZN (Astrazeneca)     BA (Boeing)           BABA (Alibaba)")
    print("BAC (Bank of America) BIDU (Baidu)          FB (Facebook)")
    print("FRA40 (CAC 40)        GE (General Electric) GER30 (DAX 30)")
    print("GLW (Corning)         GOOGL (Alphabet)      GS (Goldman Sachs)")
    print("HKG33 (Hang Seng)     JNJ (Johnson & John)  JPN225 (Nikkei 225)")
    print("LMT (Lockheed Martin) MA (Mastercard)       META (Meta Platforms)")
    print("MRK (Merck and Co)    NAS100 (Nasdaq)       NATGAS (Natural GAS)")
    print("NFLX (Netflix)        OIL (Nymex)           PFE (Pfizer)")
    print("SPX500 (SP500)        TSLA (Tesla)          TWTR (Twitter)")
    print("UK100 (FTSE 100)      UKOIL (Brent)         USA30 (DOW 30)")
    print("V (Visa)")

    print("\n--- CRYPTOCURRENCY (BASE TOKENS) ---")
    print("ADA (Cardano)         ATOM (Atom)           AVAX (Avalanche)")
    print("AXS (Axis infinity)   BCH (Bitcoin Cash)    BNB (Binance Coin)")
    print("BTC (Bitcoin)         BTG (Bitcoin Gold)    BUSD (Binance USD)")
    print("DAI (DAI)             DASH (Dashcoin)       DOGE (DogeCoin)")
    print("DOT (Polkadot)        EGLD (Elrond Egold)   ENJ (ENJ)")
    print("EOS (EOS Platform)    ETC (Ethereum Classic) ETH (Ethereum)")
    print("FIL (Filecoin)        FLOW (Flow)           FTM (Fantom USD)")
    print("FTT (FTX Token)       GALA (Gala)           HBAR (Hbar)")
    print("HNT (Helium)          ICP (Internet Comp)   LINK (Chainlink)")
    print("LRC (Loopring)        LTC (Litecoin)        LUNA (Luna)")
    print("MANA (Decentraland)   NEAR (Near)           NEO (NEO)")
    print("POL (Polygon)         ROSE (Rose)           SAND (Sandbox)")
    print("SHIB (Shiba inu)      SOL (Solana)          THETA (Theta)")
    print("TRX (Tron)            UNI (Uniswap)         USDT (Tether)")
    print("UST (Terra USD)       VET (Vechain)         XLM (Stellar)")
    print("XMR (Monero)          XRP (Ripple)          XTZ (Tezos)")
    print("=======================================================\n")

# ==========================================
# 1. HARDCODED CONFIGURATION
# ==========================================

# Enter your TraderMade API keys here:
REST_API_KEY = "REST_API_KEY"
WS_API_KEY = "WS_API_KEY"

# Define the symbols you want to stream:
SYMBOLS_TO_STREAM = ["EURUSD", "GBPUSD", "USA30"]

# Number of days of history to fetch (Max 180):
DAYS_BACK = 2

# ------------------------------------------

base_path = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(base_path, "history_tracker.json")

DAYS_BACK = min(int(DAYS_BACK), 180)

CFD_SYMBOLS = {
    "AAPL", "AMZN", "AUS200", "AZN", "BA", "BABA", "BAC", "BIDU", "FB", "FRA40",
    "GE", "GER30", "GLW", "GOOGL", "GS", "HKG33", "JNJ", "JPN225", "LMT", "MA",
    "META", "MRK", "NAS100", "NATGAS", "NFLX", "OIL", "PFE", "SPX500", "TSLA",
    "TWTR", "UK100", "UKOIL", "USA30", "V"
}

INTERVAL = "minute"
PERIOD = 1
CHUNK_DAYS = 1 if INTERVAL == "minute" else 10

mt5_conn = None
ws_session_start_time = {} 

sync_state = {} 
first_seen_minute = {}
last_print_time = {}

# ==========================================
# 2. HISTORICAL BACKFILL & REST API
# ==========================================
def delete_mt5_ticks(symbol, start_dt, end_dt):
    start_ms = int((start_dt.replace(tzinfo=timezone.utc).timestamp() - 60) * 1000)
    end_ms = int((end_dt.replace(tzinfo=timezone.utc).timestamp() + 60) * 1000)
    
    payload = f"D,{symbol},{start_ms},{end_ms}|"
    try:
        mt5_conn.sendall(payload.encode('utf-8'))
        print(f"🧹 [{symbol}] Sent command to clear old WS ticks between {start_ms} and {end_ms}.")
    except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
        raise Exception("MT5_DISCONNECTED")
    except Exception:
        pass

def fetch_data_chunked(symbol, start_time, end_time):
    all_quotes = []
    current_start = start_time
    
    # ADD THIS: Add USD suffix for CFDs for the API request
    api_symbol = symbol + "USD" if symbol in CFD_SYMBOLS else symbol
    
    while current_start < end_time:
        current_end = current_start + timedelta(days=CHUNK_DAYS)
        if current_end > end_time: current_end = end_time
            
        str_start = current_start.strftime("%Y-%m-%d-%H:%M")
        str_end = current_end.strftime("%Y-%m-%d-%H:%M")
        
        url = "https://marketdata.tradermade.com/api/v1/timeseries-beta"
        params = {
            "api_key": REST_API_KEY, "currency": api_symbol, "format": "records", # USE api_symbol HERE
            "start_date": str_start, "end_date": str_end, 
            "interval": INTERVAL, "period": PERIOD
        }
        
        try:
            response = requests.get(url, params=params)
            data = response.json()
            if "quotes" in data:
                all_quotes.extend(data["quotes"])
                print(f"[{symbol}] Downloaded chunk: {str_start} to {str_end} ({len(data['quotes'])} bars)")
            elif "message" in data:
                print(f"API Limit Warning: {data['message']}")
        except Exception as e:
            print(f"Request failed: {e}")
            
        current_start = current_end
        time.sleep(0.5) 
        
    return all_quotes

def fetch_and_inject_history(symbol):
    global ws_session_start_time
    end_time = datetime.utcnow()
    target_start_time = end_time - timedelta(days=DAYS_BACK)
    
    tracker = {}
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            tracker = json.load(f)
            
    quotes_to_inject = []
    
    if symbol in tracker:
        oldest_saved = datetime.strptime(tracker[symbol]['oldest'], "%Y-%m-%d %H:%M:%S")
        latest_saved = datetime.strptime(tracker[symbol]['latest'], "%Y-%m-%d %H:%M:%S")
        
        if target_start_time < oldest_saved:
            print(f"\n---> Expanding history for {symbol} backwards...")
            older_quotes = fetch_data_chunked(symbol, target_start_time, oldest_saved)
            quotes_to_inject.extend(older_quotes)
            tracker[symbol]['oldest'] = target_start_time.strftime("%Y-%m-%d %H:%M:%S")
            
        if (end_time - latest_saved).total_seconds() > 120:
            print(f"\n---> Fetching new recent data for {symbol} since {latest_saved}...")
            delete_mt5_ticks(symbol, latest_saved, end_time)
            
            newer_quotes = fetch_data_chunked(symbol, latest_saved, end_time)
            quotes_to_inject.extend(newer_quotes)
            tracker[symbol]['latest'] = end_time.strftime("%Y-%m-%d %H:%M:%S")
        else:
            print(f"[{symbol}] Recent data is perfectly up to date.")
            
    else:
        print(f"\n---> No memory found. Fetching full {DAYS_BACK} days of history for {symbol}...")
        quotes_to_inject = fetch_data_chunked(symbol, target_start_time, end_time)
        tracker[symbol] = {
            'oldest': target_start_time.strftime("%Y-%m-%d %H:%M:%S"),
            'latest': end_time.strftime("%Y-%m-%d %H:%M:%S")
        }

    ws_session_start_time[symbol] = end_time

    if not quotes_to_inject:
        return

    quotes_to_inject = sorted(quotes_to_inject, key=lambda x: x['date'])
    injected_count = 0
    
    for quote in quotes_to_inject:
        try:
            date_str = quote['date']
            
            # THE BULLETPROOF FIX: Handle all weird TraderMade date formats
            if len(date_str) == 10: 
                # If it's just "YYYY-MM-DD", add midnight
                date_str += " 00:00:00"
            elif len(date_str) == 16:
                # If it's "YYYY-MM-DD HH:MM" (missing seconds), add seconds
                date_str += ":00"
                
            dt_obj = datetime.strptime(date_str, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
            ts = int(dt_obj.timestamp())
            o, h, l, c = quote['open'], quote['high'], quote['low'], quote['close']
            payload = f"R,{symbol},{ts},{o},{h},{l},{c}|"
            mt5_conn.sendall(payload.encode('utf-8'))
            injected_count += 1
            
        except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
            raise Exception("MT5_DISCONNECTED")
        except Exception as e:
            # THIS IS CRITICAL: Print the error so we know if it fails!
            print(f"[!] Skipped bad candle for {symbol}: {e} | Data: {quote}")

    print(f"✅ SUCCESS! Injected {injected_count} historical candles for {symbol}.")
    with open(STATE_FILE, "w") as f:
        json.dump(tracker, f)

def fetch_single_skipped_candle(symbol, timestamp_sec):
    dt = datetime.utcfromtimestamp(timestamp_sec)
    str_start = dt.strftime("%Y-%m-%d-%H:%M")
    str_end = (dt + timedelta(minutes=1)).strftime("%Y-%m-%d-%H:%M")
    
    url = "https://marketdata.tradermade.com/api/v1/timeseries"
    params = {
        "api_key": REST_API_KEY, "currency": symbol, "format": "records",
        "start_date": str_start, "end_date": str_end, 
        "interval": "minute", "period": 1
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if "quotes" in data and len(data["quotes"]) > 0:
            q = data["quotes"][0] 
            o, h, l, c = q['open'], q['high'], q['low'], q['close']
            payload = f"R,{symbol},{timestamp_sec},{o},{h},{l},{c}|"
            mt5_conn.sendall(payload.encode('utf-8'))
            print(f"✅ [{symbol}] Successfully backfilled skipped candle for {str_start} via REST.")
    except Exception as e:
        print(f"[!] [{symbol}] Failed to fetch skipped candle: {e}")

# ==========================================
# 3. LIVE WEBSOCKET STREAM
# ==========================================
def on_error(ws, error):
    print(f"\n[WEBSOCKET ERROR] {error}")

def on_close(ws, close_status_code, close_msg):
    print(f"\n[WEBSOCKET CLOSED] The connection was closed.")
    print(f"Status Code: {close_status_code} | Message: {close_msg}")

def on_message(ws, message):
    global sync_state, first_seen_minute, last_print_time
    if "bid" not in message:
        print(f"\n[TRADERMADE SERVER SAYS]: {message}")
    try:
        data = json.loads(message)
        ws_symbol = data.get('symbol')
        bid = data.get('bid')
        ask = data.get('ask') 
        ts_ms = data.get('ts') 
        
        symbol = ws_symbol
        for original_sym in SYMBOLS_TO_STREAM:
            if original_sym in CFD_SYMBOLS and ws_symbol == f"{original_sym}USD":
                symbol = original_sym
                break
        
        if symbol and bid and ask and ts_ms:
            minute_ts_sec = (int(ts_ms) // 60000) * 60 
            
            if symbol not in sync_state:
                sync_state[symbol] = 'waiting'
                first_seen_minute[symbol] = minute_ts_sec
                last_print_time[symbol] = 0
                
            if sync_state[symbol] == 'waiting':
                if minute_ts_sec == first_seen_minute[symbol]:
                    current_time = time.time()
                    if current_time - last_print_time[symbol] > 10:
                        print(f"⏳ [{symbol}] Catching up! Waiting for the next clean M1 candle to start...")
                        last_print_time[symbol] = current_time
                    return 
                else:
                    print(f"\n🚀 [{symbol}] Fresh candle started! Pulling the old candle via REST...")
                    fetch_single_skipped_candle(symbol, first_seen_minute[symbol])
                    sync_state[symbol] = 'synced'
            
            payload_T = f"T,{symbol},{bid},{ask},{ts_ms}|"
            try:
                mt5_conn.sendall(payload_T.encode('utf-8'))
            except (ConnectionAbortedError, ConnectionResetError, BrokenPipeError):
                print("\n[!] MT5 disconnected. Please restart.")
                ws.close()
                
    except json.JSONDecodeError:
        pass

def on_open(ws):
    print("\n>>> History Complete! Transitioning to Live WebSocket Feed...")
    ws_symbols = []
    for sym in SYMBOLS_TO_STREAM:
        if sym in CFD_SYMBOLS:
            ws_symbols.append(sym + "USD")
        else:
            ws_symbols.append(sym)
            
    pairs_string = ",".join(ws_symbols)
    payload = {"userKey": WS_API_KEY, "symbol": pairs_string}
    ws.send(json.dumps(payload))

# ==========================================
# 4. MAIN EXECUTION FLOW
# ==========================================
if __name__ == "__main__":
    
    print("\n=======================================================")
    user_choice = input("Press 1 + Enter to see the supported symbols list, or just press Enter to start: ")
    if user_choice.strip() == "1":
        print_symbol_guide()
        
    HOST = '127.0.0.1'
    PORT = 9090
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1) 
    server.bind((HOST, PORT))
    server.listen(1)

    try:
        while True:
            mt5_conn = None
            sync_state = {} 
            
            print("Waiting for MT5 to connect... (Go drag your UltraLight EA onto a NORMAL broker chart!)")
            mt5_conn, addr = server.accept()
            print("MT5 Connected! Sending symbol configuration...")
            
            try:
                setup_payload = "S," + ",".join(SYMBOLS_TO_STREAM) + "|"
                mt5_conn.sendall(setup_payload.encode('utf-8'))
                time.sleep(0.5) 
                
                print("Starting automated backfill sequence...")
                for sym in SYMBOLS_TO_STREAM:
                    fetch_and_inject_history(sym)
                    time.sleep(1) 
            except Exception as e:
                if str(e) == "MT5_DISCONNECTED":
                    print("\n[!] MT5 disconnected during setup!")
                    print("[!] CRITICAL RULE: You MUST place the EA on a standard broker chart (like normal EURUSD), NOT your Custom Symbol chart!")
                    if mt5_conn:
                        try: mt5_conn.close()
                        except: pass
                    time.sleep(3)
                    continue
                else:
                    raise e
                
            print("\nAttempting to connect to WebSocket...")
            ws = websocket.WebSocketApp(
                "wss://marketdata.tradermade.com/feedadv", 
                on_message=on_message, 
                on_open=on_open,
                on_error=on_error,
                on_close=on_close
            )
            ws.run_forever()
            
            if mt5_conn:
                try: mt5_conn.close()
                except: pass
            time.sleep(2)
            
    except KeyboardInterrupt:
        print("\n[!] Script stopped by user.")
    except Exception as e:
        print(f"\n[CRITICAL ERROR] The script crashed during execution:")
        print(f"Error Details: {e}")
        traceback.print_exc()
    finally:
        print("\n=========================================")
        print(" RUNNING CLEANUP BEFORE EXIT...")
        print("=========================================")
        
        if mt5_conn:
            try: mt5_conn.close()
            except: pass
                
        if os.path.exists(STATE_FILE):
            try:
                with open(STATE_FILE, "r") as f:
                    tracker = json.load(f)
                    
                for symbol in SYMBOLS_TO_STREAM:
                    if symbol in tracker and symbol in ws_session_start_time:
                        revert_time = ws_session_start_time[symbol]
                        tracker[symbol]['latest'] = revert_time.strftime("%Y-%m-%d %H:%M:%S")
                        print(f"[{symbol}] Erasing WS session from memory.")
                
                with open(STATE_FILE, "w") as f:
                    json.dump(tracker, f, indent=4)
            except Exception as e:
                print(f"Error updating state file: {e}")
                
        print("✅ Cleanup complete.")
        input("\nPress Enter to exit the window...")
