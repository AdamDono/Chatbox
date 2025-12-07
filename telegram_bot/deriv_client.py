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
        self.active_contracts = {} # {contract_id: {symbol, type, stake, buy_price}}
        self.balance = 0
        self.result_callback = None # Function to call when trade closes

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
                if len(self.tick_history[symbol]) > 100: # Keep 100 ticks for better analysis
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
                contract_id = data['buy']['contract_id']
                buy_price = data['buy']['buy_price']
                print(f"DEBUG: Buy response received for contract {contract_id}")
                # Update balance from buy response if available
                if 'balance_after' in data['buy']:
                    self.balance = data['buy']['balance_after']
                    print(f"✅ Trade Executed! Contract ID: {contract_id}, Buy Price: ${buy_price}, Balance: ${self.balance}")
                else:
                    print(f"✅ Trade Executed! Contract ID: {contract_id}, Buy Price: ${buy_price}")
                    # Request balance if not in response
                    await self.get_balance()
                
                # Subscribe to this contract to get updates
                print(f"DEBUG: Subscribing to contract {contract_id} for updates...")
                await self.subscribe_contract(contract_id)
        
        elif msg_type == "proposal_open_contract":
            # Contract status update
            contract = data.get('proposal_open_contract', {})
            contract_id = contract.get('contract_id', 'unknown')
            is_sold = contract.get('is_sold', False)
            print(f"DEBUG: Contract update for {contract_id}, is_sold={is_sold}")
            
            if is_sold:
                # Contract closed!
                sell_price = contract.get('sell_price', 0)
                buy_price = contract.get('buy_price', 0)
                profit = sell_price - buy_price
                status = contract.get('status', 'unknown')
                
                print(f"📊 Contract {contract_id} closed: Profit=${profit:.2f}, Status={status}")
                
                # Request fresh balance after trade closes
                await self.get_balance()
                await asyncio.sleep(0.3)  # Wait for balance update
                
                # Notify via callback
                print(f"DEBUG: Calling result_callback for contract {contract_id}...")
                if self.result_callback:
                    await self.result_callback(contract, profit)
                else:
                    print(f"DEBUG: result_callback is None!")
        
        elif msg_type == "balance":
            # Balance update
            print(f"DEBUG: Received balance message from Deriv: {data}")
            self.balance = data['balance']['balance']
            print(f"💰 Balance Updated: ${self.balance}")

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
    
    def set_result_callback(self, callback):
        """Set callback for trade results"""
        self.result_callback = callback
    
    async def subscribe_contract(self, contract_id):
        """Subscribe to contract updates to track when it closes"""
        print(f"DEBUG: Sending subscription request for contract {contract_id}")
        req = {
            "proposal_open_contract": 1,
            "contract_id": contract_id,
            "subscribe": 1
        }
        await self.send(req)
        print(f"DEBUG: Subscription request sent for contract {contract_id}")
    
    async def get_balance(self):
        """Request current balance"""
        print("DEBUG: Requesting balance from Deriv...")
        req = {"balance": 1, "subscribe": 1}
        await self.send(req)
        print(f"DEBUG: Balance request sent. Current balance value: ${self.balance}")

deriv_client = DerivClient()
