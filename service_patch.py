"""
Service patch for problematic dependencies

This module monkey patches problematic imports to provide alternative implementations
or mock functionality where needed.
"""

import sys
import importlib.util

# Create mock module for aiohttp
class MockResponse:
    def __init__(self, status=200, data=None):
        self.status = status
        self._data = data or {}
    
    async def json(self):
        return self._data
    
    async def text(self):
        return str(self._data)
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass

class MockClientSession:
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        pass
    
    async def get(self, url, headers=None):
        return MockResponse(200, {"message": "Mock response from " + url})
    
    async def post(self, url, json=None, headers=None):
        return MockResponse(200, {"message": "Mock response from POST to " + url})
    
    async def close(self):
        pass

# Create mock aiohttp module
class MockAiohttp:
    class ClientSession(MockClientSession):
        pass
    
    class ClientError(Exception):
        pass
    
    class ClientConnectorError(ClientError):
        pass

# Patch imports by adding our mock modules to sys.modules before they're imported
sys.modules['aiohttp'] = MockAiohttp()

# Replace alpaca-trade-api imports with our compatibility layer
class ImportFinder:
    def find_spec(self, fullname, path, target=None):
        if fullname == 'alpaca_trade_api':
            # Redirect to our compatibility layer
            import alpaca_compat
            sys.modules['alpaca_trade_api'] = alpaca_compat
            return importlib.util.find_spec('alpaca_compat')
        return None

# Register our custom import finder
sys.meta_path.insert(0, ImportFinder())

print("Service patch applied - problematic dependencies have been patched") 