import json
import logging
from kafka import KafkaConsumer

from app.config import get_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def main() -> None:
    settings = get_settings()
    if not settings.kafka_enabled:
        raise SystemExit("Set KAFKA_ENABLED=true in .env before starting the consumer.")

    consumer = KafkaConsumer(
        settings.kafka_topic,
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        auto_offset_reset="earliest",
        enable_auto_commit=True,
        group_id="document-qa-events",
        value_deserializer=lambda value: json.loads(value.decode("utf-8")),
    )
    logger.info("Listening for events on topic %s", settings.kafka_topic)
    try:
        for message in consumer:
            logger.info("Received document event: %s", message.value)
    finally:
        consumer.close()


if __name__ == "__main__":
    main()
