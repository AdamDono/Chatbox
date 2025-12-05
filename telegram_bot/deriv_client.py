import asyncio
import json
import websockets
import config
import time

class DerivClient:
    def __init__(self):
        self.ws_url = f"wss://ws.binaryws.com/websockets/v3?app_id={config.DERIV_APP_ID}"
        self.websocket = None
        self.token = config.DERIV_API_TOKEN
        self.authorized = False
        self.tick_history = {} # {symbol: [price1, price2]}
        self.callbacks = [] # Functions to call on tick update

    async def connect(self):
        try:
            self.websocket = await websockets.connect(self.ws_url)
            print("Connected to Deriv WebSocket")
            await self.authorize()
        except Exception as e:
            print(f"Connection Error: {e}")

    async def authorize(self):
        auth_req = {"authorize": self.token}
        await self.send(auth_req)

    async def send(self, data):
        if self.websocket:
            await self.websocket.send(json.dumps(data))

    async def listen(self):
        while True:
            try:
                async for message in self.websocket:
                    data = json.loads(message)
                    await self.handle_message(data)
            except Exception as e:
                print(f"Listen Error: {e}. Reconnecting in 5 seconds...")
                self.websocket = None
                self.authorized = False
                await asyncio.sleep(5)
                await self.connect()

    async def handle_message(self, data):
        msg_type = data.get("msg_type")

        if msg_type == "authorize":
            print(f"Authorized: {data['authorize']['email']}")
            self.authorized = True
            # Subscribe to ticks after auth
            symbols = list(config.SYMBOLS.values())
            print(f"Subscribing to: {symbols}")
            await self.subscribe_ticks(symbols)

        elif msg_type == "tick":
            try:
                tick = data['tick']
                symbol = tick['symbol']
                price = tick['quote']
                epoch = tick['epoch']
                
                print(f"✓ Tick: {symbol} = {price}")  # Debug: Show all ticks
                
                # Update history
                if symbol not in self.tick_history:
                    self.tick_history[symbol] = []
                self.tick_history[symbol].append(price)
                if len(self.tick_history[symbol]) > 60: # Keep 60 ticks
                    self.tick_history[symbol].pop(0)

                # Notify callbacks
                for callback in self.callbacks:
                    await callback(symbol, price, self.tick_history[symbol])
            except KeyError as e:
                print(f"Tick parsing error: Missing key {e} in data: {data}")
            except Exception as e:
                print(f"Tick processing error: {e}")
        
        elif "error" in data:
            print(f"Deriv API Error: {data['error']}")

        elif msg_type == "proposal":
            # Handle trade proposal
            if "error" in data:
                print(f"Proposal Error: {data['error']['message']}")
            else:
                proposal_id = data['proposal']['id']
                await self.buy_contract(proposal_id)

        elif msg_type == "buy":
            if "error" in data:
                print(f"Buy Error: {data['error']['message']}")
            else:
                print(f"Trade Executed! Contract ID: {data['buy']['contract_id']}")
                # Notify Telegram (will be handled by callback)

    async def subscribe_ticks(self, symbols):
        req = {"ticks": symbols}
        await self.send(req)

    async def propose_trade(self, symbol, contract_type):
        # contract_type: "CALL" (Rise) or "PUT" (Fall)
        req = {
            "proposal": 1,
            "amount": config.STAKE_AMOUNT,
            "basis": "stake",
            "contract_type": contract_type,
            "currency": "USD",
            "duration": config.DURATION_SECONDS,
            "duration_unit": "s",
            "symbol": symbol
        }
        await self.send(req)

    async def buy_contract(self, proposal_id):
        req = {
            "buy": proposal_id,
            "price": 100 # Max price, safe to put high for buy
        }
        await self.send(req)

    def add_tick_callback(self, callback):
        self.callbacks.append(callback)

deriv_client = DerivClient()
