from datetime import datetime, timezone
import json
import logging
import os
from typing import Callable, Dict, List, Optional
from sqlalchemy import select
from backend.database import get_db_session
from backend.models import OutboxEvent, ProcessedEvent
from utils.config import settings

logger = logging.getLogger(__name__)

# Topics required by specification
TOPIC_ORDER_CREATED = f"{settings.KAFKA_TOPIC_PREFIX}order.created"
TOPIC_INVENTORY_UPDATED = f"{settings.KAFKA_TOPIC_PREFIX}inventory.updated"
TOPIC_PRODUCT_UPDATED = f"{settings.KAFKA_TOPIC_PREFIX}product.updated"
TOPIC_SHOP_UPDATED = f"{settings.KAFKA_TOPIC_PREFIX}shop.updated"

EVENT_TYPE_TO_TOPIC = {
    "order.created": TOPIC_ORDER_CREATED,
    "OrderConfirmed": TOPIC_ORDER_CREATED,
    "order.status_updated": TOPIC_ORDER_CREATED,
    "inventory.updated": TOPIC_INVENTORY_UPDATED,
    "product.created": TOPIC_PRODUCT_UPDATED,
    "product.updated": TOPIC_PRODUCT_UPDATED,
    "shop.approved": TOPIC_SHOP_UPDATED,
    "shop.created": TOPIC_SHOP_UPDATED,
    "shop.updated": TOPIC_SHOP_UPDATED,
    "ShopRegistered": TOPIC_SHOP_UPDATED,
}


class KafkaEventProducer:
    """Kafka event publisher utilizing confluent-kafka with SASL/SSL or local plaintext support."""

    def __init__(self):
        self._producer = None
        self._last_error = None
        self._init_producer()

    def _init_producer(self):
        if not settings.KAFKA_BOOTSTRAP_SERVERS:
            self._last_error = "KAFKA_BOOTSTRAP_SERVERS not set"
            return

        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "client.id": f"{settings.APP_NAME}-producer",
            "acks": "all",
            "retries": 2,
            "socket.timeout.ms": 3000,
            "message.timeout.ms": 5000,
        }

        if settings.KAFKA_USERNAME and settings.KAFKA_PASSWORD:
            conf.update(
                {
                    "security.protocol": settings.KAFKA_SECURITY_PROTOCOL,
                    "sasl.mechanism": settings.KAFKA_SASL_MECHANISM,
                    "sasl.username": settings.KAFKA_USERNAME,
                    "sasl.password": settings.KAFKA_PASSWORD,
                }
            )

        ca_loc = settings.KAFKA_CA_LOCATION
        if ca_loc and os.path.exists(ca_loc):
            try:
                with open(ca_loc, "r", encoding="utf-8") as f:
                    content = f.read()
                if "-----BEGIN CERTIFICATE-----" in content:
                    conf["ssl.ca.location"] = os.path.abspath(ca_loc)
            except Exception as e:
                logger.debug("Could not read CA file %s: %s", ca_loc, e)

        try:
            from confluent_kafka import Producer

            self._producer = Producer(conf)
            self._last_error = None
        except Exception as exc:
            self._last_error = str(exc)
            logger.warning("Failed to initialize confluent_kafka Producer: %s", exc)
            self._producer = None

    @property
    def is_connected(self) -> bool:
        return self._producer is not None and self._last_error is None

    @property
    def last_error(self) -> Optional[str]:
        return self._last_error

    def publish(self, topic: str, key: str, payload: dict) -> bool:
        """Publish JSON message to Kafka topic. Returns False gracefully if offline."""
        if not self._producer:
            return False

        try:
            value_bytes = json.dumps(payload, default=str).encode("utf-8")
            key_bytes = key.encode("utf-8") if key else None

            delivery_error = []

            def _on_delivery(err, msg):
                if err is not None:
                    delivery_error.append(err)
                    logger.error("Message delivery failed: %s", err)

            self._producer.produce(topic, key=key_bytes, value=value_bytes, on_delivery=_on_delivery)
            self._producer.flush(timeout=3.0)
            success = len(delivery_error) == 0
            if not success:
                self._last_error = str(delivery_error[0])
            return success
        except Exception as exc:
            self._last_error = str(exc)
            logger.error("Exception during Kafka publish to %s: %s", topic, exc)
            return False


producer = KafkaEventProducer()


def relay_outbox_events(limit: int = 50) -> int:
    """Transactional Outbox Relay: fetch pending outbox records from PostgreSQL, publish to Kafka, mark as published."""
    relayed_count = 0
    with get_db_session() as session:
        events = (
            session.execute(
                select(OutboxEvent)
                .where(OutboxEvent.status == "PENDING")
                .order_by(OutboxEvent.created_at.asc())
                .limit(limit)
            )
            .scalars()
            .all()
        )

        for event in events:
            topic = EVENT_TYPE_TO_TOPIC.get(event.event_type, f"{settings.KAFKA_TOPIC_PREFIX}{event.event_type}")
            try:
                payload = json.loads(event.payload)
            except Exception:
                payload = {"raw": event.payload}

            success = producer.publish(topic, key=event.aggregate_id, payload=payload)
            if success:
                event.status = "PUBLISHED"
                event.published_at = datetime.now(timezone.utc)
                relayed_count += 1
        session.flush()
    return relayed_count


class KafkaEventConsumer:
    """Kafka event consumer supporting idempotent consumption and consumer group management."""

    def __init__(self, group_id: Optional[str] = None, topics: Optional[List[str]] = None):
        self.group_id = group_id or settings.KAFKA_CONSUMER_GROUP
        self.topics = topics or list(EVENT_TYPE_TO_TOPIC.values())
        self._consumer = None

    def _init_consumer(self):
        if not settings.KAFKA_BOOTSTRAP_SERVERS:
            return None

        conf = {
            "bootstrap.servers": settings.KAFKA_BOOTSTRAP_SERVERS,
            "group.id": self.group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": False,
            "socket.timeout.ms": 3000,
        }

        if settings.KAFKA_USERNAME and settings.KAFKA_PASSWORD:
            conf.update(
                {
                    "security.protocol": settings.KAFKA_SECURITY_PROTOCOL,
                    "sasl.mechanism": settings.KAFKA_SASL_MECHANISM,
                    "sasl.username": settings.KAFKA_USERNAME,
                    "sasl.password": settings.KAFKA_PASSWORD,
                }
            )

        ca_loc = settings.KAFKA_CA_LOCATION
        if ca_loc and os.path.exists(ca_loc):
            try:
                with open(ca_loc, "r", encoding="utf-8") as f:
                    content = f.read()
                if "-----BEGIN CERTIFICATE-----" in content:
                    conf["ssl.ca.location"] = os.path.abspath(ca_loc)
            except Exception as e:
                logger.debug("Could not read CA file %s: %s", ca_loc, e)

        try:
            from confluent_kafka import Consumer

            consumer = Consumer(conf)
            consumer.subscribe(self.topics)
            self._consumer = consumer
            return consumer
        except Exception as exc:
            logger.warning("Failed to initialize Kafka Consumer: %s", exc)
            return None

    def process_event_idempotently(self, event_id: str, handler: Callable[[dict], None], payload: dict) -> bool:
        """Idempotency check: ensures an event_id is only processed once per consumer group."""
        with get_db_session() as session:
            already_processed = session.execute(
                select(ProcessedEvent).where(
                    ProcessedEvent.event_id == event_id,
                    ProcessedEvent.consumer_group == self.group_id,
                )
            ).scalar_one_or_none()

            if already_processed:
                logger.info("Skipping duplicate event ID %s in group %s.", event_id, self.group_id)
                return False

            # Execute business logic (e.g. OpenSearch index update or order notification)
            handler(payload)

            # Record processing record
            session.add(
                ProcessedEvent(
                    event_id=event_id,
                    consumer_group=self.group_id,
                    processed_at=datetime.now(timezone.utc),
                )
            )
            session.flush()
            return True
