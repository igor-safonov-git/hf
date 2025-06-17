"""
Adapter to make HuntflowVirtualEngine compatible with SQLAlchemy AsyncEngine interface
"""
from typing import Any, Dict
from contextlib import asynccontextmanager


class AsyncEngineAdapter:
    """Wraps HuntflowVirtualEngine to provide AsyncEngine-like interface"""
    
    def __init__(self, virtual_engine):
        self.virtual_engine = virtual_engine
        
    @asynccontextmanager
    async def begin(self):
        """Provide async context manager interface expected by views"""
        yield AsyncConnectionAdapter(self.virtual_engine)


class AsyncConnectionAdapter:
    """Adapts virtual engine to connection-like interface"""
    
    def __init__(self, virtual_engine):
        self.virtual_engine = virtual_engine
        
    async def execute(self, query):
        """Execute query using virtual engine"""
        # The virtual engine expects execute_sqlalchemy_query
        result = await self.virtual_engine.execute_sqlalchemy_query(query)
        # Return a result-like object that can be iterated
        return AsyncResultAdapter(result)