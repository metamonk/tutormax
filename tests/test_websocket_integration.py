"""
Integration tests for WebSocket real-time dashboard updates.

Tests the complete WebSocket flow:
- Connection/disconnection
- Message broadcasting
- Reconnection logic
- Data consistency
"""

import pytest
import asyncio
import json
from typing import List

from src.api.websocket_service import ConnectionManager


class TestWebSocketIntegration:
    """
    Test suite for WebSocket integration.
    """

    @pytest.fixture
    def connection_manager(self):
        """Create fresh connection manager for each test."""
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_connection_manager_broadcast(self, connection_manager):
        """Test ConnectionManager broadcast functionality."""
        # Create mock WebSocket connections
        connections_received = []

        class MockWebSocket:
            def __init__(self, id):
                self.id = id
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, message):
                self.messages.append(json.loads(message))

        # Add connections
        ws1 = MockWebSocket("ws1")
        ws2 = MockWebSocket("ws2")

        await connection_manager.connect(ws1)
        await connection_manager.connect(ws2)

        assert connection_manager.get_connection_count() == 2

        # Broadcast message
        test_data = {"test": "data", "value": 123}
        await connection_manager.broadcast("test_message", test_data)

        # Both connections should receive the message
        assert len(ws1.messages) == 1
        assert len(ws2.messages) == 1

        assert ws1.messages[0]["type"] == "test_message"
        assert ws1.messages[0]["data"] == test_data
        assert "timestamp" in ws1.messages[0]

        # Disconnect one connection
        await connection_manager.disconnect(ws1)
        assert connection_manager.get_connection_count() == 1

        # Broadcast again
        await connection_manager.broadcast("second_message", {"test": "data2"})

        # Only ws2 should receive
        assert len(ws1.messages) == 1  # Still 1 (not connected)
        assert len(ws2.messages) == 2  # Received second message

    @pytest.mark.asyncio
    async def test_connection_manager_personal_message(self, connection_manager):
        """Test ConnectionManager personal message functionality."""

        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, message):
                self.messages.append(json.loads(message))

        ws = MockWebSocket()
        await connection_manager.connect(ws)

        # Send personal message
        test_data = {"personal": "message"}
        await connection_manager.send_personal(ws, "personal_test", test_data)

        assert len(ws.messages) == 1
        assert ws.messages[0]["type"] == "personal_test"
        assert ws.messages[0]["data"] == test_data


    @pytest.mark.asyncio
    async def test_websocket_error_handling(self):
        """Test WebSocket error handling and recovery."""

        class FailingWebSocket:
            def __init__(self):
                self.accept_count = 0
                self.send_count = 0

            async def accept(self):
                self.accept_count += 1

            async def send_text(self, message):
                self.send_count += 1
                # Simulate error on second send
                if self.send_count >= 2:
                    raise RuntimeError("Connection error")

        manager = ConnectionManager()
        ws = FailingWebSocket()

        await manager.connect(ws)
        assert manager.get_connection_count() == 1

        # First broadcast should succeed
        await manager.broadcast("test1", {"data": "1"})

        # Second broadcast should fail but not crash
        await manager.broadcast("test2", {"data": "2"})

        # Connection should be automatically removed after error
        assert manager.get_connection_count() == 0




class TestWebSocketMessageTypes:
    """
    Tests for different WebSocket message types.
    """

    @pytest.fixture
    def connection_manager(self):
        return ConnectionManager()

    @pytest.mark.asyncio
    async def test_metrics_update_message(self, connection_manager):
        """Test metrics_update message format."""

        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, message):
                self.messages.append(json.loads(message))

        ws = MockWebSocket()
        await connection_manager.connect(ws)

        metrics_data = {
            "tutor_id": "T001",
            "window": "30day",
            "avg_rating": 4.5,
            "sessions_completed": 20,
        }

        await connection_manager.broadcast("metrics_update", metrics_data)

        assert len(ws.messages) == 1
        message = ws.messages[0]

        assert message["type"] == "metrics_update"
        assert message["data"] == metrics_data
        assert "timestamp" in message

    @pytest.mark.asyncio
    async def test_alert_message(self, connection_manager):
        """Test alert message format."""

        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, message):
                self.messages.append(json.loads(message))

        ws = MockWebSocket()
        await connection_manager.connect(ws)

        alert_data = {
            "id": "ALERT-001",
            "severity": "critical",
            "tutor_id": "T001",
            "message": "High churn risk detected",
        }

        await connection_manager.broadcast("alert", alert_data)

        message = ws.messages[0]
        assert message["type"] == "alert"
        assert message["data"]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_intervention_message(self, connection_manager):
        """Test intervention message format."""

        class MockWebSocket:
            def __init__(self):
                self.messages = []

            async def accept(self):
                pass

            async def send_text(self, message):
                self.messages.append(json.loads(message))

        ws = MockWebSocket()
        await connection_manager.connect(ws)

        intervention_data = {
            "id": "INT-001",
            "tutor_id": "T001",
            "type": "coaching",
            "status": "pending",
        }

        await connection_manager.broadcast("intervention", intervention_data)

        message = ws.messages[0]
        assert message["type"] == "intervention"
        assert message["data"]["status"] == "pending"


# Note: Full end-to-end WebSocket tests with TestClient require
# the complete app to be importable. For full integration tests,
# see docs/WEBSOCKET_TESTING_GUIDE.md for manual testing procedures.
