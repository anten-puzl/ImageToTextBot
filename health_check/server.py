# health_check/server.py
from aiohttp import web
import logging
from core.config import HEALTH_CHECK_PORT

logger = logging.getLogger(__name__)

async def health_check(request):
    """Simple health check endpoint."""
    logger.debug("Health check requested")
    return web.Response(text="OK", status=200)

async def run_health_check_server():
    """Runs the aiohttp server for health checks."""
    app = web.Application()
    app.add_routes([
        web.get('/', health_check),
        web.get('/health', health_check)
    ])
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, '0.0.0.0', HEALTH_CHECK_PORT)
    try:
        await site.start()
        logger.info(f"Health check server started on http://0.0.0.0:{HEALTH_CHECK_PORT}/health")
        return runner
    except OSError as e:
        logger.error(f"Failed to start health check server on port {HEALTH_CHECK_PORT}: {e}")
        return None