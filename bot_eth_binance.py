import ccxt, os, pandas as pd, ta

KEY=os.getenv('BINANCE_API_KEY')
SECRET=os.getenv('BINANCE_API_SECRET')
SYMBOL='ETH/USDC'

exchange = ccxt.binance({
    'apiKey': KEY,
    'secret': SECRET,
    'enableRateLimit': True,
    'options': {
        'defaultType': 'spot',
        'fetchCurrencies': False,
        'adjustForTimeDifference': True
    },
    'urls': {
        'api': {
            'public': 'https://data-api.binance.vision/api/v3',
            'private': 'https://api.binance.com/api/v3',
            'sapi': 'https://api.binance.com/sapi/v1',
        }
    }
})

def check():
    try:
        exchange.load_markets()
        candles=exchange.fetch_ohlcv(SYMBOL, '2h', limit=100)
    except Exception as e:
        print(f"Error fetch OHLCV con binance.vision, probando con api.binance.com: {e}")
        # fallback sin el truco de vision
        exchange2 = ccxt.binance({
            'apiKey': KEY, 'secret': SECRET,
            'enableRateLimit': True,
            'options': {'defaultType':'spot','fetchCurrencies':False}
        })
        candles=exchange2.fetch_ohlcv(SYMBOL, '2h', limit=100)

    df=pd.DataFrame(candles, columns=['t','o','h','l','c','v'])
    df['rsi']=ta.momentum.RSIIndicator(df['c']).rsi()
    df['ema200']=ta.trend.EMAIndicator(df['c'], 200).ema_indicator()
    
    last=df.iloc[-1]
    price=last['c']
    rsi=last['rsi']
    ema=last['ema200']
    
    print(f"Precio: {price} RSI: {rsi} EMA200: {ema}")
    
    if rsi < 30 and price > ema:
        print("SEÑAL DE COMPRA!")
        try:
            bal=exchange.fetch_balance()
            usdc=bal['USDC']['free'] if 'USDC' in bal else 0
            print(f"USDC disponible: {usdc}")
            if usdc > 11:
                order=exchange.create_market_buy_order(SYMBOL, 11/usdc*usdc/price) # compra 11 USDC
                # más simple: comprar 11 USDC en ETH
                # order=exchange.create_market_buy_order(SYMBOL, 11/price)
                print(f"COMPRA EJECUTADA: {order}")
            else:
                # intenta comprar con todo si es menos de 11
                if usdc > 1:
                    order=exchange.create_market_buy_order(SYMBOL, usdc*0.99/price)
                    print(f"COMPRA con saldo disponible: {order}")
                else:
                    print("Sin USDC suficiente")
        except Exception as e:
            print(f"Error en compra: {e}")
    else:
        print("No hay señal de compra")

check()
