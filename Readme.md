# TraderMade MT5 Data Bridge

A professional-grade, hybrid market data bridge connecting the TraderMade API to MetaTrader 5 (MT5).

## 🚀 Installation

Create a folder for your project, download the repository files, and install the required Python packages.

```bash
mkdir MT5_Data_Bridge
cd MT5_Data_Bridge
pip install requests websocket-client

```

## 🛠️ Project Setup

Before running the bridge, you need to add your API keys and configure MetaTrader 5.

**1. Set up your API Keys**
Open `main.py` and paste your TraderMade REST and WebSocket API keys at the very top of the script:

```python
REST_API_KEY = "YOUR_REST_KEY_HERE"
WS_API_KEY = "YOUR_WS_KEY_HERE"
SYMBOLS_TO_STREAM = ["EURUSD", "GBPUSD", "USA30"]
DAYS_BACK = 2

```

> **⚠️ Security Warning:** Because your API keys are hardcoded, do not commit or push `main.py` to a public GitHub repository without removing your keys first!

**2. Set up the MT5 EA**

1. Open MT5 and press **F4** to open the MetaEditor.
2. In the `Experts/Advisors` folder, create a new file named `TraderMade_UltraLight_Receiver.mq5`.
3. Paste the MQL5 code from this repository and press **F7** to compile.

**3. Allow MT5 Network Permissions**
In MT5, go to **Tools > Options** (**Ctrl+O**). Under the **Expert Advisors** tab, check **Allow algorithmic trading** and click OK.

---

## 🔑 Getting Started

First, run the Python script to start the local TCP server. It will download your history and wait for MT5.

```bash
python main.py

```

*(Wait for the console to say: `Waiting for MT5 to connect...`)*

---

## 💻 Usage Instructions

> **Zero-Coding Quick Start:**
> If you don't want to install Python, you can download the pre-compiled `.exe` version of this bridge directly from our **[Releases](https://www.google.com/search?q=%23)**.

After starting the Python script, making the connection to MT5 is easy.

### 1. Attach the EA

Open the MT5 Navigator (**Ctrl+N**) and drag the `TraderMade_UltraLight_Receiver` EA onto a **STANDARD broker chart** (e.g., your default EURUSD chart).

🚨 *Do NOT attach the EA to the Custom Symbol charts it creates, or the connection will fail.*

### 2. Open Your Custom Charts

Once connected, Python will dynamically create custom symbols and feed the data to MT5. Open your Market Watch (**Ctrl+M**), look for your new custom symbols (ending in `_TRADERMADE10`), right-click them, and select **Chart Window**.

### 3. Graceful Cleanup

If you need to stop the script, simply press `Ctrl+C` in your terminal. The Python script will cleanly update its `history_tracker.json` memory state before exiting, ensuring smooth continuity on your next run.

---

## 📡 The Custom Protocol (For Developers)

The Python server and MQL5 client communicate over TCP port `9090` using a custom, pipe-delimited string protocol:

```text
S,EURUSD,GBPUSD|                          // Setup Custom Symbols
R,EURUSD,1678453200,1.05,1.06,1.04,1.05|  // Inject M1 REST candles
T,EURUSD,1.0510,1.0512,1678453200500|     // Inject live WS ticks
D,EURUSD,1678450000000,1678453200000|     // Delete overlapping ticks

```