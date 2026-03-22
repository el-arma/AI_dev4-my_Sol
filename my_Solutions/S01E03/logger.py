import logging
from fastapi import Request
import time
import uuid


# Configure logging once
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
)

logger = logging.getLogger("api")

async def logging_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())
    request.state.request_id = request_id

    start_time = time.time()

    try:
        response = await call_next(request)
        status_code = response.status_code
    except Exception as e:
        duration = (time.time() - start_time) * 1000

        logger.exception(
            f"{request.method} {request.url.path} "
            f"status=500 "
            f"time={duration:.2f}ms "
            f"req_id={request_id} "
            f"error={str(e)}"
        )
        raise

    duration = (time.time() - start_time) * 1000

    logger.info(
        f"{request.method} {request.url.path} "
        f"status={status_code} "
        f"time={duration:.2f}ms "
        f"req_id={request_id}"
    )

    return response