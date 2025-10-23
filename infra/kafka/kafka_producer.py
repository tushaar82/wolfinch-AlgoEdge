#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: Kafka Producer for Event Streaming
 Copyright: (c) 2024 Wolfinch Contributors
'''

import json
from datetime import datetime
from kafka import KafkaProducer
from kafka.errors import KafkaError

from utils import getLogger

log = getLogger('KafkaProducer')
log.setLevel(log.INFO)


class WolfinchKafkaProducer:
    """
    Kafka Producer for publishing trading events
    Ensures reliable, ordered, auditable event streaming
    """

    # Kafka topics
    TOPICS = {
        'ORDERS_SUBMITTED': 'wolfinch.orders.submitted',
        'ORDERS_EXECUTED': 'wolfinch.orders.executed',
        'ORDERS_REJECTED': 'wolfinch.orders.rejected',
        'TRADES_COMPLETED': 'wolfinch.trades.completed',
        'POSITIONS_UPDATED': 'wolfinch.positions.updated',
        'RISKS_BREACHED': 'wolfinch.risks.breached',
        'SYSTEM_ALERTS': 'wolfinch.system.alerts',
        'MARKET_DATA': 'wolfinch.market.data'
    }

    def __init__(self, bootstrap_servers='localhost:9093', enabled=True):
        self.enabled = enabled
        self.bootstrap_servers = bootstrap_servers
        self.producer = None

        if self.enabled:
            self._init_producer()

    def _init_producer(self):
        """Initialize Kafka producer"""
        try:
            self.producer = KafkaProducer(
                bootstrap_servers=self.bootstrap_servers,
                value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                key_serializer=lambda k: k.encode('utf-8') if k else None,
                acks='all',  # Wait for all replicas
                retries=3,
                max_in_flight_requests_per_connection=1,  # Ensure ordering
                compression_type='gzip',
                linger_ms=10,  # Batch messages for 10ms
                buffer_memory=33554432,  # 32MB buffer
            )
            log.info(f"Kafka producer initialized: {self.bootstrap_servers}")
        except Exception as e:
            log.error(f"Failed to initialize Kafka producer: {e}")
            self.enabled = False

    def _create_event(self, event_type, data):
        """Create standardized event format"""
        return {
            'event_type': event_type,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }

    def _send_event(self, topic, key, event):
        """Send event to Kafka topic"""
        if not self.enabled or not self.producer:
            log.warning("Kafka producer disabled, event not sent")
            return False

        try:
            future = self.producer.send(topic, key=key, value=event)
            # Block for 'synchronous' sends
            record_metadata = future.get(timeout=10)

            log.debug(f"Event sent: {topic} partition={record_metadata.partition} "
                     f"offset={record_metadata.offset}")
            return True

        except KafkaError as e:
            log.error(f"Failed to send event to {topic}: {e}")
            return False
        except Exception as e:
            log.error(f"Unexpected error sending event: {e}")
            return False

    # ================== Event Publishing Methods ==================

    def publish_order_submitted(self, order):
        """Publish order submission event"""
        event = self._create_event('ORDER_SUBMITTED', {
            'order_id': order.get('id'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'quantity': order.get('quantity'),
            'price': order.get('price'),
            'order_type': order.get('order_type'),
            'strategy': order.get('strategy')
        })

        return self._send_event(
            self.TOPICS['ORDERS_SUBMITTED'],
            key=order.get('id'),
            event=event
        )

    def publish_order_executed(self, order):
        """Publish order execution event"""
        event = self._create_event('ORDER_EXECUTED', {
            'order_id': order.get('id'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'quantity': order.get('quantity'),
            'executed_price': order.get('executed_price'),
            'execution_time': order.get('execution_time'),
            'broker_order_id': order.get('broker_order_id')
        })

        return self._send_event(
            self.TOPICS['ORDERS_EXECUTED'],
            key=order.get('id'),
            event=event
        )

    def publish_order_rejected(self, order, reason):
        """Publish order rejection event"""
        event = self._create_event('ORDER_REJECTED', {
            'order_id': order.get('id'),
            'symbol': order.get('symbol'),
            'side': order.get('side'),
            'quantity': order.get('quantity'),
            'price': order.get('price'),
            'rejection_reason': reason,
            'timestamp': datetime.now().isoformat()
        })

        return self._send_event(
            self.TOPICS['ORDERS_REJECTED'],
            key=order.get('id'),
            event=event
        )

    def publish_trade_completed(self, trade):
        """Publish trade completion event"""
        event = self._create_event('TRADE_COMPLETED', {
            'trade_id': trade.get('trade_id'),
            'symbol': trade.get('symbol'),
            'side': trade.get('side'),
            'quantity': trade.get('quantity'),
            'entry_price': trade.get('entry_price'),
            'exit_price': trade.get('exit_price'),
            'pnl': trade.get('pnl'),
            'commission': trade.get('commission'),
            'strategy': trade.get('strategy')
        })

        return self._send_event(
            self.TOPICS['TRADES_COMPLETED'],
            key=trade.get('trade_id'),
            event=event
        )

    def publish_position_updated(self, position):
        """Publish position update event"""
        event = self._create_event('POSITION_UPDATED', {
            'symbol': position.get('symbol'),
            'quantity': position.get('quantity'),
            'entry_price': position.get('entry_price'),
            'current_price': position.get('current_price'),
            'unrealized_pnl': position.get('unrealized_pnl'),
            'trailing_sl': position.get('trailing_sl')
        })

        return self._send_event(
            self.TOPICS['POSITIONS_UPDATED'],
            key=position.get('symbol'),
            event=event
        )

    def publish_risk_breached(self, risk_event):
        """Publish risk breach event"""
        event = self._create_event('RISK_BREACHED', {
            'breach_type': risk_event.get('type'),
            'current_value': risk_event.get('current_value'),
            'limit_value': risk_event.get('limit_value'),
            'action_taken': risk_event.get('action'),
            'severity': risk_event.get('severity', 'HIGH')
        })

        return self._send_event(
            self.TOPICS['RISKS_BREACHED'],
            key=risk_event.get('type'),
            event=event
        )

    def publish_system_alert(self, alert):
        """Publish system alert event"""
        event = self._create_event('SYSTEM_ALERT', {
            'alert_type': alert.get('type'),
            'severity': alert.get('severity'),
            'message': alert.get('message'),
            'details': alert.get('details')
        })

        return self._send_event(
            self.TOPICS['SYSTEM_ALERTS'],
            key=alert.get('type'),
            event=event
        )

    def publish_market_data(self, market_data):
        """Publish market data event"""
        event = self._create_event('MARKET_DATA', market_data)

        return self._send_event(
            self.TOPICS['MARKET_DATA'],
            key=market_data.get('symbol'),
            event=event
        )

    def flush(self):
        """Flush any pending messages"""
        if self.producer:
            self.producer.flush()

    def close(self):
        """Close Kafka producer"""
        if self.producer:
            self.producer.flush()
            self.producer.close()
            log.info("Kafka producer closed")


# Global Kafka producer instance
_kafka_producer = None


def get_kafka_producer():
    """Get global Kafka producer instance"""
    global _kafka_producer
    if _kafka_producer is None:
        _kafka_producer = WolfinchKafkaProducer()
    return _kafka_producer


# EOF
