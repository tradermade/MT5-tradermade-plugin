//+------------------------------------------------------------------+
//|                            TraderMade_UltraLight_Receiver.mq5    |
//+------------------------------------------------------------------+
#property copyright "Python Master Bridge - Live WS & REST"
#property version   "9.00" // Upgraded to Dynamic Symbol Creation

// Notice: InpSymbols is GONE! Python is in control now.
input string Suffix = "_TRADERMADE10";

int client_socket = INVALID_HANDLE;

int OnInit()
  {
   client_socket = SocketCreate();
   if(client_socket != INVALID_HANDLE)
     {
      if(SocketConnect(client_socket, "127.0.0.1", 9090, 1000))
        {
         Print("Successfully connected to Python Master Bridge! Waiting for instructions...");
         EventSetMillisecondTimer(10); 
        }
      else Print("TCP Connection failed! Start Python script first.");
     }
   return(INIT_SUCCEEDED);
  }

void OnDeinit(const int reason)
  {
   EventKillTimer();
   if(client_socket != INVALID_HANDLE) SocketClose(client_socket);
  }

void OnTimer()
  {
   if(client_socket == INVALID_HANDLE) return;
   
   uint len = SocketIsReadable(client_socket);
   if(len > 0)
     {
      uchar u_buffer[]; 
      if(SocketRead(client_socket, u_buffer, len, 100) > 0)
        {
         string chunk = CharArrayToString(u_buffer);
         static string data_buffer = ""; 
         data_buffer += chunk;
         
         int pipe_pos = StringFind(data_buffer, "|");
         while(pipe_pos >= 0)
           {
            string payload = StringSubstr(data_buffer, 0, pipe_pos);
            data_buffer = StringSubstr(data_buffer, pipe_pos + 1);
            
            if(payload != "")
              {
               string comp[];
               int c_count = StringSplit(payload, ',', comp);
               
               if(c_count > 0)
                 {
                  
               // Phase 0: S = Setup (Dynamic Symbol Creation)
                  if(comp[0] == "S")
                    {
                     for(int i = 1; i < c_count; i++)
                       {
                        string raw_sym = comp[i];
                        StringTrimLeft(raw_sym);
                        StringTrimRight(raw_sym);
                        
                        if(raw_sym != "")
                          {
                           string custom_name = raw_sym + Suffix;
                           CustomSymbolCreate(custom_name, "", raw_sym);
                           
                           // ---> THE FIX: Tell MT5 to draw the chart using pure Bid prices! <---
                           CustomSymbolSetInteger(custom_name, SYMBOL_CHART_MODE, SYMBOL_CHART_MODE_BID);
                           
                           SymbolSelect(custom_name, true);
                           Print("✅ Auto-created custom symbol: ", custom_name);
                          }
                       }
                    }
                  // Phase 1: R = Rate (History M1 Candle from REST)
                  else if(comp[0] == "R" && c_count == 7)
                    {
                     string custom_name = comp[1] + Suffix;
                     MqlRates rate[1];
                     rate[0].time = (datetime)StringToInteger(comp[2]);
                     rate[0].open = StringToDouble(comp[3]);
                     rate[0].high = StringToDouble(comp[4]);
                     rate[0].low  = StringToDouble(comp[5]);
                     rate[0].close= StringToDouble(comp[6]);
                     rate[0].tick_volume = 1;
                     CustomRatesUpdate(custom_name, rate);
                    }
                  // Phase 2: T = Tick (Live Stream from WebSocket)
                  else if(comp[0] == "T" && c_count == 5)
                    {
                     string custom_name = comp[1] + Suffix;
                     MqlTick tick[1];
                     tick[0].time = (datetime)(StringToInteger(comp[4]) / 1000);
                     tick[0].time_msc = (long)StringToInteger(comp[4]);
                     tick[0].bid = StringToDouble(comp[2]);
                     tick[0].ask = StringToDouble(comp[3]);
                     tick[0].flags = TICK_FLAG_BID | TICK_FLAG_ASK;
                     
                     CustomTicksAdd(custom_name, tick);
                     SymbolInfoDouble(custom_name, SYMBOL_BID); 
                    }
                  // Phase 3: D = Delete Ticks (Wipe WS session on overlap)
                  else if(comp[0] == "D" && c_count == 4)
                    {
                     string custom_name = comp[1] + Suffix;
                     long start_ms = (long)StringToInteger(comp[2]);
                     long end_ms   = (long)StringToInteger(comp[3]);
                     
                     CustomTicksDelete(custom_name, start_ms, end_ms);
                    }
                 }
              }
            pipe_pos = StringFind(data_buffer, "|");
           }
        }
     }
  }
//+------------------------------------------------------------------+