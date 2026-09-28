import ccxt, pandas as pd, time, os
from ta.trend import EMAIndicator
from ta.momentum import RSIIndicator

SYMBOL='ETH/USDT'; TIMEFRAME='2h'; LEVERAGE=3; USDT_AMOUNT=50
TP1=2.5; TP2=5.0; SL=2.0

exchange=ccxt.binance({'apiKey':os.getenv('BINANCE_API_KEY'),'secret':os.getenv('BINANCE_API_SECRET'),'options':{'defaultType':'future'}})

def get_signal():
 candles=exchange.fetch_ohlcv(SYMBOL,TIMEFRAME,limit=100)
 df=pd.DataFrame(candles,columns=['time','open','high','low','close','vol'])
 df['ema20']=EMAIndicator(df['close'],20).ema_indicator()
 df['ema50']=EMAIndicator(df['close'],50).ema_indicator()
 df['rsi']=RSIIndicator(df['close'],14).rsi()
 last=df.iloc[-1]; prev=df.iloc[-2]
 if prev['ema20']<prev['ema50'] and last['ema20']>last['ema50'] and last['rsi']>50: return 'buy'
 return None

while True:
 try:
  sig=get_signal()
  print(f"Chequeo 2h - {sig}")
  if sig=='buy':
   pos=exchange.fetch_positions([SYMBOL])
   if not any(float(p.get('contracts',0))>0 for p in pos):
    exchange.set_leverage(LEVERAGE,SYMBOL)
    price=exchange.fetch_ticker(SYMBOL)['last']
    qty=(USDT_AMOUNT*LEVERAGE)/price
    exchange.create_market_buy_order(SYMBOL,qty)
    exchange.create_order(SYMBOL,'TAKE_PROFIT_MARKET','sell',qty*0.6,None,{'stopPrice':price*(1+TP1/100)})
    exchange.create_order(SYMBOL,'TAKE_PROFIT_MARKET','sell',qty*0.4,None,{'stopPrice':price*(1+TP2/100)})
    exchange.create_order(SYMBOL,'STOP_MARKET','sell',qty,None,{'stopPrice':price*(1-SL/100)})
  time.sleep(7200)
 except Exception as e:
  print(e); time.sleep(60)