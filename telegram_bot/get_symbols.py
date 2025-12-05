import asyncio
import json
import websockets

DERIV_APP_ID = 1089

async def get_symbols():
    url = f"wss://ws.binaryws.com/websockets/v3?app_id={DERIV_APP_ID}"
    async with websockets.connect(url) as websocket:
        req = {"active_symbols": "brief", "product_type": "basic"}
        await websocket.send(json.dumps(req))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        if "error" in data:
            print("Error:", data["error"])
            return

        symbols = data["active_symbols"]
        print(f"Found {len(symbols)} symbols.")
        
        targets = ["Boom", "Crash", "Tech", "US"]
        for s in symbols:
            display_name = s["display_name"]
            if any(t in display_name for t in targets):
                print(f"{display_name}: {s['symbol']}")

asyncio.run(get_symbols())
