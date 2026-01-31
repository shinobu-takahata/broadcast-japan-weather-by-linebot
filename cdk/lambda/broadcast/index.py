import json
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


def handler(event, context):
    logger.info("Broadcast handler invoked")
    logger.info(f"Event: {json.dumps(event)}")

    return {"statusCode": 200, "message": "Broadcast completed"}
