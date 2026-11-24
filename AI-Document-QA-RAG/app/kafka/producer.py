import json
from kafka import KafkaProducer
from kafka.errors import KafkaError

from app.config import get_settings


def publish_document_event(document_id: str, filename: str, chunks: int) -> bool:
    settings = get_settings()
    if not settings.kafka_enabled:
        return False

    producer = KafkaProducer(
        bootstrap_servers=settings.kafka_bootstrap_servers.split(","),
        value_serializer=lambda value: json.dumps(value).encode("utf-8"),
        retries=3,
    )
    try:
        future = producer.send(settings.kafka_topic, {
            "event": "document.indexed",
            "document_id": document_id,
            "filename": filename,
            "chunks": chunks,
        })
        future.get(timeout=10)
        producer.flush()
        return True
    except KafkaError:
        raise
    finally:
        producer.close()
