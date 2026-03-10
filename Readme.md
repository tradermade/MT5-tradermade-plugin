
---

```markdown
# MT5 Smart Data Bridge: Hybrid REST & WebSocket Plugin (TraderMade)

A professional-grade, low-latency market data bridge connecting [TraderMade's](https://tradermade.com) financial data APIs to MetaTrader 5 (MT5). 

This pipeline acts as a "Smart Bridge," pulling bulk historical minute-candles via the REST API for chart context, and seamlessly transitioning to the WebSocket API for sub-second, real-time tick injection. All data is routed through a local Python TCP server into a lightweight MT5 Expert Advisor (EA).



## ✨ Key Features

* **Dynamic Symbol Creation:** Python instructs MT5 to automatically create Custom Symbols (e.g., `EURUSD_TRADERMADE10`) directly in your Market Watch.
* **Hybrid Data Ingestion:** Combines historical backfilling (REST) with live tick streaming (WebSockets).
* **State Memory & Gap Handling:** Uses `history_tracker.json` to remember the last downloaded candle, saving API calls and seamlessly filling "transition gaps" when switching to live WebSockets.
* **UltraLight MQL5 Receiver:** The MT5 EA does no heavy lifting. It acts strictly as a high-speed TCP string parser to draw charts.
* **Strict UTC Timezone Management:** Ensures flawless candle alignment within the MT5 database.

---

## 🛠️ Prerequisites

1. **Python 3.7+** installed on your machine.
2. **MetaTrader 5 (MT5)** desktop terminal.
3. **TraderMade API Keys:** You need both a REST API key and a WebSocket API key from your [TraderMade dashboard](https://tradermade.com/signup).

---

## 🚀 Installation & Setup

### 1. Python Environment Setup
Clone this repository or download the files to a local directory. Open your terminal in that directory and install the required Python libraries:

```bash
pip install requests websocket-client

```

### 2. MQL5 EA Setup

1. Open MT5 and press **F4** to open the MetaEditor.
2. In the `Experts/Advisors` folder, create a new file named `TraderMade_UltraLight_Receiver.mq5`.
3. Paste the provided MQL5 code into this file.
4. Press **F7** to compile. Ensure there are zero errors.

### 3. Network Permissions in MT5

To allow MT5 to connect to the local Python server:

1. Go to **Tools > Options** (**Ctrl+O**) in MT5.
2. Navigate to the **Expert Advisors** tab.
3. Check **Allow algorithmic trading**.
4. Click **OK**.

---

## 💻 Usage Instructions

### Step 1: Add Your API Keys to the Script

Open the Python script (e.g., `tm_bridge.py`) in any text editor. Locate the `# 1. HARDCODED CONFIGURATION` section near the top of the file and paste your API keys. You can also adjust your symbols and history length here:

```python
# ==========================================
# 1. HARDCODED CONFIGURATION
# ==========================================

# Enter your TraderMade API keys here:
REST_API_KEY = "YOUR_REST_KEY_HERE"
WS_API_KEY = "YOUR_WS_KEY_HERE"

# Define the symbols you want to stream:
SYMBOLS_TO_STREAM = ["EURUSD", "GBPUSD", "USA30"]

# Number of days of history to fetch (Max 180):
DAYS_BACK = 2

```

> ⚠️ **Security Warning:** Because your API keys are hardcoded into the Python file, **do not commit or push this file to public GitHub repositories** without removing your keys first!

### Step 2: Start the Bridge

Run the Python script in your terminal. It will start the local TCP server and wait for MT5.

```bash
python tm_bridge.py

```

*Console output will say: `Waiting for MT5 to connect...*`

### Step 3: Connect the MT5 EA (CRITICAL)

In MT5, open the Navigator (**Ctrl+N**). Drag the `TraderMade_UltraLight_Receiver` EA onto a **STANDARD broker chart** (e.g., your broker's default EURUSD chart).

🚨 **CRITICAL RULE:** Do **NOT** attach the EA to the Custom Symbol charts it creates, or the connection will fail!

### Step 4: Open Your Custom Charts

Once connected, Python will feed the data to MT5. Open your Market Watch (**Ctrl+M**), look for your new custom symbols (ending in `_TRADERMADE10`), right-click them, and select **Chart Window**.

---

## 📡 The Custom String Protocol (For Developers)

The Python server and MQL5 client communicate over TCP port `9090` using a custom, pipe-delimited string protocol:

* **`S` (Setup):** `S,EURUSD,GBPUSD|` -> Triggers dynamic symbol creation.
* **`R` (Rates):** `R,EURUSD,1678453200,1.05,1.06,1.04,1.05|` -> Injects historical M1 REST candles.
* **`T` (Ticks):** `T,EURUSD,1.0510,1.0512,1678453200500|` -> Injects live WebSocket Bid/Ask ticks.
* **`D` (Delete):** `D,EURUSD,1678450000000,1678453200000|` -> Deletes overlapping ticks during transitions.

---

## 🛑 Cleanup & Exit

If you need to stop the script, simply press `Ctrl+C` in your terminal or close the window. The Python script has a built-in fallback to cleanly update its memory state before exiting, ensuring smooth continuity on your next run.

