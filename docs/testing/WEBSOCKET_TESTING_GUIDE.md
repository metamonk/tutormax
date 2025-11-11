# WebSocket Integration Testing Guide

This guide provides comprehensive instructions for testing the WebSocket real-time dashboard functionality.

## Overview

TutorMax uses WebSocket connections to provide real-time updates to the operations dashboard, including:
- **Tutor performance metrics** - Real-time performance updates
- **Critical alerts** - Immediate notifications of issues
- **Intervention tasks** - Live intervention queue updates
- **Analytics** - Dashboard analytics refreshed in real-time

## WebSocket Architecture

### Backend (FastAPI)
- **Endpoint**: `/ws/dashboard`
- **Protocol**: WebSocket (ws:// or wss://)
- **Connection Manager**: Handles multiple concurrent connections
- **Message Types**: `metrics_update`, `alert`, `intervention`, `analytics_update`

### Frontend (Next.js/React)
- **Hook**: `useWebSocket()` - React hook for WebSocket connection
- **Service**: `WebSocketService` - Manages connection, reconnection, and message handling
- **Auto-reconnection**: Automatic reconnection with exponential backoff (up to 10 attempts)

## Running Tests

### Backend Tests

Run WebSocket integration tests:

```bash
# Run all WebSocket tests
pytest tests/test_websocket_integration.py -v

# Run with coverage
pytest tests/test_websocket_integration.py --cov=src/api/websocket_router --cov=src/api/websocket_service

# Run specific test class
pytest tests/test_websocket_integration.py::TestWebSocketIntegration -v

# Run end-to-end tests only
pytest tests/test_websocket_integration.py -m integration
```

### Manual Testing

#### 1. Using Browser DevTools

1. Start the API server:
   ```bash
   uvicorn src.api.main:app --reload
   ```

2. Open browser console and connect:
   ```javascript
   const ws = new WebSocket('ws://localhost:8000/ws/dashboard');

   ws.onopen = () => console.log('Connected');
   ws.onmessage = (event) => {
     const data = JSON.parse(event.data);
     console.log('Received:', data);
   };
   ws.onerror = (error) => console.error('Error:', error);
   ws.onclose = () => console.log('Disconnected');

   // Send ping
   ws.send('ping');
   ```

#### 2. Using wscat (CLI tool)

Install wscat:
```bash
npm install -g wscat
```

Connect and test:
```bash
# Connect to WebSocket
wscat -c ws://localhost:8000/ws/dashboard

# You'll receive initial analytics immediately

# Send ping
> ping

# You should receive pong response
< {"type":"analytics_update","data":{"pong":true},"timestamp":"2025-01-10T..."}
```

#### 3. Using Python WebSocket Client

```python
import asyncio
import websockets
import json

async def test_websocket():
    uri = "ws://localhost:8000/ws/dashboard"

    async with websockets.connect(uri) as websocket:
        print("Connected!")

        # Receive initial analytics
        message = await websocket.recv()
        data = json.loads(message)
        print(f"Received: {data['type']}")
        print(json.dumps(data['data'], indent=2))

        # Send ping
        await websocket.send("ping")

        # Receive pong
        response = await websocket.recv()
        pong_data = json.loads(response)
        print(f"Pong: {pong_data}")

# Run test
asyncio.run(test_websocket())
```

## Testing Scenarios

### 1. Basic Connection Test

**Objective**: Verify WebSocket connection establishes successfully

**Steps**:
1. Connect to `/ws/dashboard`
2. Verify connection accepted (status 101)
3. Verify initial analytics message received
4. Verify message has correct structure

**Expected Result**:
- Connection established
- Initial message received within 1 second
- Message has `type`, `data`, and `timestamp` fields

### 2. Ping/Pong Keep-Alive Test

**Objective**: Verify keep-alive mechanism works

**Steps**:
1. Connect to WebSocket
2. Send text message "ping"
3. Wait for response

**Expected Result**:
- Receive `analytics_update` message with `{"pong": true}`

### 3. Multiple Connections Test

**Objective**: Verify server can handle multiple concurrent connections

**Steps**:
1. Open 10 concurrent WebSocket connections
2. Verify all receive initial analytics
3. Check `/ws/status` endpoint shows correct count
4. Close 5 connections
5. Verify status updates

**Expected Result**:
- All connections established successfully
- Status reflects accurate connection count
- No crashes or errors

### 4. Reconnection Test

**Objective**: Verify automatic reconnection works

**Frontend Test**:
1. Connect to WebSocket
2. Monitor network tab
3. Restart backend server
4. Observe automatic reconnection attempts
5. Verify reconnection succeeds

**Expected Result**:
- Frontend detects disconnection
- Reconnection attempts logged
- Successfully reconnects when server available
- No data loss

### 5. Message Broadcasting Test

**Objective**: Verify broadcast messages reach all clients

**Steps**:
1. Connect 3 WebSocket clients
2. Trigger a broadcast event (e.g., new metrics update)
3. Verify all 3 clients receive the message

**Backend Simulation**:
```python
from src.api.websocket_service import get_connection_manager

manager = get_connection_manager()
await manager.broadcast("test_message", {"test": "data"})
```

**Expected Result**:
- All connected clients receive the message
- Message format is correct
- Timestamp is current

### 6. Connection Error Handling Test

**Objective**: Verify graceful handling of connection errors

**Steps**:
1. Connect to WebSocket
2. Simulate network interruption (kill connection)
3. Verify frontend handles error gracefully
4. Verify automatic reconnection

**Expected Result**:
- No JavaScript errors
- User sees connection status indicator
- Automatic reconnection attempts

### 7. Load Test

**Objective**: Verify performance under load

**Steps**:
1. Connect 100 concurrent WebSocket connections
2. Send broadcasts every second
3. Monitor memory and CPU usage
4. Verify no connections drop

**Expected Result**:
- All connections remain stable
- Broadcast latency < 100ms
- Memory usage stable
- No connection timeouts

## Frontend Testing

### React Testing Library Tests

```typescript
// tests/websocket.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useWebSocket } from '@/hooks/useWebSocket';

describe('useWebSocket', () => {
  it('should connect and receive initial data', async () => {
    const { result } = renderHook(() => useWebSocket());

    await waitFor(() => {
      expect(result.current.state.connected).toBe(true);
      expect(result.current.state.analytics).not.toBeNull();
    });
  });

  it('should handle disconnection', async () => {
    const { result } = renderHook(() => useWebSocket());

    // Simulate disconnection
    // ... (mock WebSocket)

    await waitFor(() => {
      expect(result.current.state.connected).toBe(false);
    });
  });
});
```

### E2E Testing with Playwright

```typescript
// tests/e2e/dashboard.spec.ts
import { test, expect } from '@playwright/test';

test('dashboard receives real-time updates', async ({ page }) => {
  await page.goto('http://localhost:3000/dashboard');

  // Wait for WebSocket connection
  await page.waitForSelector('[data-testid="connection-indicator"][data-status="connected"]');

  // Verify initial analytics loaded
  const tutorCount = await page.textContent('[data-testid="total-tutors"]');
  expect(parseInt(tutorCount)).toBeGreaterThan(0);

  // Trigger backend update (via API)
  // ...

  // Verify dashboard updates
  await expect(page.locator('[data-testid="alert-badge"]')).toContainText('1');
});
```

## Monitoring WebSocket Health

### Metrics to Monitor

1. **Active Connections**
   - Endpoint: `GET /ws/status`
   - Check every 30 seconds

2. **Connection Duration**
   - Average time connections stay open
   - Target: > 5 minutes

3. **Reconnection Rate**
   - Number of reconnections per hour
   - Target: < 10

4. **Message Latency**
   - Time from broadcast to client receipt
   - Target: < 100ms

5. **Error Rate**
   - WebSocket errors per 1000 messages
   - Target: < 0.1%

### Health Check Script

```bash
#!/bin/bash
# Check WebSocket health

API_URL="http://localhost:8000"

# Check status endpoint
status=$(curl -s "$API_URL/ws/status")
connections=$(echo $status | jq -r '.active_connections')

echo "Active WebSocket Connections: $connections"

if [ "$connections" -lt 1 ]; then
  echo "⚠️  Warning: No active WebSocket connections"
else
  echo "✅ WebSocket service operational"
fi
```

## Troubleshooting

### Issue: WebSocket Connection Fails

**Symptoms**: Cannot establish connection, immediate close

**Causes**:
- CORS misconfiguration
- Firewall blocking WebSocket
- Server not running
- Wrong URL/port

**Solutions**:
1. Verify server is running: `curl http://localhost:8000/ws/status`
2. Check CORS settings in `.env`:
   ```bash
   CORS_ORIGINS=http://localhost:3000
   ```
3. Check browser console for CORS errors
4. Verify WebSocket URL uses correct protocol (ws:// vs wss://)

### Issue: Frequent Disconnections

**Symptoms**: Connection drops every few seconds

**Causes**:
- Network instability
- Server timeout too aggressive
- Load balancer timeout
- Client-side reconnection bug

**Solutions**:
1. Check server logs for errors
2. Increase timeout settings
3. Verify reconnection logic
4. Test with direct server connection (bypass load balancer)

### Issue: Messages Not Received

**Symptoms**: Connected but no updates

**Causes**:
- Broadcasting not triggered
- Message handler error
- Serialization error

**Solutions**:
1. Check server logs for broadcast calls
2. Verify message format is valid JSON
3. Check client message handler for errors
4. Test with manual broadcast

### Issue: Memory Leak

**Symptoms**: Memory usage increases over time

**Causes**:
- Connections not properly cleaned up
- Message handlers not removed
- Event listeners not unsubscribed

**Solutions**:
1. Verify `disconnect()` is called on unmount
2. Check for leaked subscriptions
3. Profile memory with Chrome DevTools
4. Review connection cleanup logic

## Production Checklist

- [ ] Load test with expected number of concurrent users
- [ ] Test reconnection with production infrastructure
- [ ] Monitor WebSocket connection count in production
- [ ] Set up alerts for connection anomalies
- [ ] Configure WebSocket timeout appropriately
- [ ] Use WSS (secure WebSocket) in production
- [ ] Test with production load balancer
- [ ] Implement connection rate limiting if needed
- [ ] Add WebSocket metrics to monitoring dashboard
- [ ] Document WebSocket firewall requirements

## Best Practices

1. **Always clean up connections** - Use context managers and cleanup handlers
2. **Implement exponential backoff** - Don't hammer server with reconnection attempts
3. **Handle partial messages** - WebSocket can fragment large messages
4. **Use heartbeat/ping** - Detect dead connections early
5. **Log connection events** - Track connections for debugging
6. **Test offline scenarios** - Verify graceful degradation
7. **Monitor connection metrics** - Track health in production
8. **Use connection pools** - Limit max connections per user
9. **Validate messages** - Don't trust client input
10. **Document message formats** - Keep schema updated

## References

- [FastAPI WebSocket Documentation](https://fastapi.tiangolo.com/advanced/websockets/)
- [WebSocket RFC 6455](https://tools.ietf.org/html/rfc6455)
- [WebSocket Best Practices](https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API)
