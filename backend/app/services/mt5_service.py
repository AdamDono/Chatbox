import sys
import platform
from app.config import settings

# Try to import MetaTrader5, if not available (e.g. on Mac), we'll use a mock
try:
    import MetaTrader5 as mt5
    HAS_MT5 = True
except ImportError:
    HAS_MT5 = False
    print("MetaTrader5 package not found. Running in Mock mode.")

class MT5Service:
    def __init__(self):
        self.connected = False
        self.mock_mode = settings.MOCK_MODE or not HAS_MT5
        self.account_info = {
            "login": settings.MT5_LOGIN,
            "balance": settings.STARTING_CAPITAL,
            "equity": settings.STARTING_CAPITAL,
            "profit": 0.0
        }

    def initialize(self):
        if self.mock_mode:
            self.connected = True
            print("MT5 Service initialized in MOCK MODE")
            return True
        
        if not mt5.initialize():
            print("initialize() failed, error code =", mt5.last_error())
            return False
        
        self.connected = True
        return True

    def login(self):
        if self.mock_mode:
            return True
        
        authorized = mt5.login(settings.MT5_LOGIN, password=settings.MT5_PASSWORD, server=settings.MT5_SERVER)
        if authorized:
            print("connected to account #{}".format(settings.MT5_LOGIN))
        else:
            print("failed to connect at account #{}, error code: {}".format(settings.MT5_LOGIN, mt5.last_error()))
        return authorized

    def get_account_info(self):
        if self.mock_mode:
            # Simulate some price movement or profit
            return self.account_info
        
        info = mt5.account_info()
        if info is None:
            return None
        return info._asdict()

    def shutdown(self):
        if self.mock_mode:
            self.connected = False
            return
        mt5.shutdown()

mt5_service = MT5Service()
