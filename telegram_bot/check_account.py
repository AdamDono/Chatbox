#!/usr/bin/env python3
"""
Quick script to verify which Deriv account the bot is connected to
"""
import asyncio
import json
import websockets

DERIV_APP_ID = 1089
DERIV_API_TOKEN = "9HYOiDPbahTFCeT"  # Your token

async def check_account():
    url = f"wss://ws.binaryws.com/websockets/v3?app_id={DERIV_APP_ID}"
    
    async with websockets.connect(url) as websocket:
        # Authorize
        auth_req = {"authorize": DERIV_API_TOKEN}
        await websocket.send(json.dumps(auth_req))
        
        response = await websocket.recv()
        data = json.loads(response)
        
        if "authorize" in data:
            auth_data = data["authorize"]
            print("\n" + "="*60)
            print("🔐 CONNECTED ACCOUNT INFORMATION")
            print("="*60)
            print(f"Email: {auth_data.get('email', 'N/A')}")
            print(f"Account ID: {auth_data.get('loginid', 'N/A')}")
            print(f"Currency: {auth_data.get('currency', 'N/A')}")
            print(f"Balance: {auth_data.get('balance', 'N/A')}")
            print(f"Account Type: {'DEMO' if 'VRTC' in auth_data.get('loginid', '') else 'REAL'}")
            print("="*60)
            
            # Get full account details
            balance_req = {"balance": 1, "subscribe": 0}
            await websocket.send(json.dumps(balance_req))
            
            balance_response = await websocket.recv()
            balance_data = json.loads(balance_response)
            
            if "balance" in balance_data:
                print(f"\n💰 Current Balance: {balance_data['balance']['balance']} {balance_data['balance']['currency']}")
            
        elif "error" in data:
            print(f"\n❌ Error: {data['error']['message']}")
        
        print("\n")

if __name__ == "__main__":
    asyncio.run(check_account())
