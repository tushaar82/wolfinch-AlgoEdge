#! /usr/bin/env python
'''
 Wolfinch Auto trading Bot
 Desc: Circuit Breaker for Fault Tolerance
 Copyright: (c) 2024 Wolfinch Contributors
'''

import time
from enum import Enum
from datetime import datetime, timedelta

from utils import getLogger

log = getLogger('CircuitBreaker')
log.setLevel(log.INFO)


class CircuitState(Enum):
    CLOSED = "CLOSED"  # Normal operation
    OPEN = "OPEN"  # Failures detected, blocking calls
    HALF_OPEN = "HALF_OPEN"  # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation
    Prevents cascading failures by temporarily blocking operations
    """

    def __init__(self, name, failure_threshold=5, recovery_timeout=60, success_threshold=2):
        """
        Args:
            name: Circuit breaker name
            failure_threshold: Number of failures before opening circuit
            recovery_timeout: Seconds to wait before trying again
            success_threshold: Consecutive successes needed to close circuit
        """
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.opened_at = None

        log.info(f"Circuit breaker created: {name}")

    def call(self, func, *args, **kwargs):
        """
        Execute function through circuit breaker

        Args:
            func: Function to execute
            *args, **kwargs: Function arguments

        Returns:
            Function result or raises CircuitBreakerError

        Raises:
            CircuitBreakerError: If circuit is OPEN
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._half_open()
            else:
                raise CircuitBreakerError(f"Circuit {self.name} is OPEN")

        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result

        except Exception as e:
            self._on_failure()
            raise e

    def _on_success(self):
        """Handle successful execution"""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            log.info(f"Circuit {self.name} HALF_OPEN: Success {self.success_count}/{self.success_threshold}")

            if self.success_count >= self.success_threshold:
                self._close()

    def _on_failure(self):
        """Handle failed execution"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        log.warning(f"Circuit {self.name}: Failure {self.failure_count}/{self.failure_threshold}")

        if self.state == CircuitState.HALF_OPEN:
            self._open()
        elif self.failure_count >= self.failure_threshold:
            self._open()

    def _should_attempt_reset(self):
        """Check if enough time has passed to attempt reset"""
        if not self.opened_at:
            return False

        elapsed = (datetime.now() - self.opened_at).total_seconds()
        return elapsed >= self.recovery_timeout

    def _close(self):
        """Close circuit - normal operation"""
        log.info(f"Circuit {self.name}: CLOSED (normal operation)")
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.opened_at = None

    def _open(self):
        """Open circuit - block all calls"""
        log.critical(f"Circuit {self.name}: OPEN (blocking calls)")
        self.state = CircuitState.OPEN
        self.opened_at = datetime.now()
        self.success_count = 0

    def _half_open(self):
        """Half-open circuit - testing recovery"""
        log.info(f"Circuit {self.name}: HALF_OPEN (testing)")
        self.state = CircuitState.HALF_OPEN
        self.success_count = 0

    def get_state(self):
        """Get current circuit state"""
        return self.state.value

    def reset(self):
        """Manually reset circuit breaker"""
        log.warning(f"Circuit {self.name}: Manual reset")
        self._close()

    def force_open(self):
        """Manually open circuit breaker"""
        log.warning(f"Circuit {self.name}: Forced OPEN")
        self._open()


class CircuitBreakerError(Exception):
    """Raised when circuit breaker is OPEN"""
    pass


# Global circuit breakers
_circuit_breakers = {}


def get_circuit_breaker(name, **kwargs):
    """Get or create circuit breaker"""
    if name not in _circuit_breakers:
        _circuit_breakers[name] = CircuitBreaker(name, **kwargs)
    return _circuit_breakers[name]


# EOF
