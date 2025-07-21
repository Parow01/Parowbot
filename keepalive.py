"""
Keep-alive service for 24/7 operation of the whale alert bot.
This creates a simple HTTP server to respond to health checks.
"""

import asyncio
import logging
from aiohttp import web
import time

class KeepAliveServer:
    """Simple HTTP server for health checks and keep-alive."""
    
    def __init__(self, port=5000):
        self.port = port
        self.app = web.Application()
        self.runner = None
        self.site = None
        self.logger = logging.getLogger(__name__)
        self.start_time = time.time()
        
        # Setup routes
        self.app.router.add_get('/', self.health_check)
        self.app.router.add_get('/health', self.health_check)
        self.app.router.add_get('/status', self.bot_status)
    
    async def health_check(self, request):
        """Health check endpoint."""
        uptime = int(time.time() - self.start_time)
        hours = uptime // 3600
        minutes = (uptime % 3600) // 60
        
        return web.json_response({
            'status': 'healthy',
            'service': 'whale-alert-bot',
            'uptime_seconds': uptime,
            'uptime_formatted': f"{hours}h {minutes}m",
            'timestamp': int(time.time())
        })
    
    async def bot_status(self, request):
        """Bot status endpoint."""
        return web.json_response({
            'bot': 'Whale Alert Bot',
            'status': 'running',
            'monitoring': 'BTC, ETH, SOL, BNB, XRP, TON, ADA',
            'uptime': int(time.time() - self.start_time)
        })
    
    async def start(self):
        """Start the keep-alive server."""
        try:
            self.runner = web.AppRunner(self.app)
            await self.runner.setup()
            
            self.site = web.TCPSite(self.runner, '0.0.0.0', self.port)
            await self.site.start()
            
            self.logger.info(f"Keep-alive server started on port {self.port}")
            
        except Exception as e:
            self.logger.error(f"Failed to start keep-alive server: {e}")
            raise
    
    async def stop(self):
        """Stop the keep-alive server."""
        try:
            if self.site:
                await self.site.stop()
            if self.runner:
                await self.runner.cleanup()
            
            self.logger.info("Keep-alive server stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping keep-alive server: {e}")

# For standalone testing
if __name__ == "__main__":
    async def main():
        server = KeepAliveServer()
        await server.start()
        
        try:
            # Keep running
            await asyncio.Event().wait()
        except KeyboardInterrupt:
            pass
        finally:
            await server.stop()
    
    asyncio.run(main())