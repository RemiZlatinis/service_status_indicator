import asyncio
import sys

from database import DB
from logger import log
from service_registry import ServiceRegistry


async def main():
    DB.initialize()
    log('Scheduler started.')
    while True:
        await ServiceRegistry.refresh_enabled_services_async()
        await asyncio.sleep(1)

if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.create_task(main())
    try:
        loop.run_forever()
    except KeyboardInterrupt:
        print('\rExecution interrupted by the user. Exiting gracefully. 🫵')
        sys.exit(0)
    finally:
        loop.close()
