from fastapi import APIRouter, HTTPException
from app.services.mt5_service import mt5_service
from app.config import settings

router = APIRouter(prefix="/api/trading", tags=["trading"])

@router.on_event("startup")
async def startup_event():
    if not mt5_service.initialize():
        print("Failed to initialize MT5 Service")

@router.get("/status")
async def get_status():
    info = mt5_service.get_account_info()
    if not info:
        raise HTTPException(status_code=500, detail="Failed to get account info")
    
    # Calculate progress
    start_balance = settings.STARTING_CAPITAL
    current_equity = info.get("equity", start_balance)
    profit = current_equity - start_balance
    profit_pct = (profit / start_balance) * 100
    
    return {
        "connected": mt5_service.connected,
        "mock_mode": mt5_service.mock_mode,
        "account": info,
        "progress": {
            "daily_profit": profit,
            "daily_profit_pct": profit_pct,
            "target_pct": settings.DAILY_PROFIT_TARGET_PCT,
            "goal_reached": profit_pct >= settings.DAILY_PROFIT_TARGET_PCT
        }
    }
