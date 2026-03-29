import time
from fastapi import Request
from logger import setup_logger


logger = setup_logger()

async def logging_middleware(request: Request, call_next):
    start = time.time()

    method = request.method
    path = request.url.path
    client_ip = request.client.host if request.client else "unknown"

    try:
        response = await call_next(request)
        status_code = response.status_code

    except Exception as e:
        status_code = 500

        logger.exception(
            f"{method} {path} status=500 ip={client_ip}"
        )

        raise e

    finally:
        duration = round((time.time() - start) * 1000, 2)

        logger.info(
            f"{method} {path} "
            f"status={status_code} "
            f"time={duration}ms "
            f"ip={client_ip}"
        )

    return response