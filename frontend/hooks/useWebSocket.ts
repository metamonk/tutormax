'use client';

/**
 * React hook for WebSocket connection and real-time updates
 */

import { useEffect, useState, useCallback, useRef } from 'react';
import { getWebSocketService } from '@/lib/websocket';
import { WebSocketMessage, DashboardState } from '@/lib/types';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws/dashboard';

export function useWebSocket() {
  const [state, setState] = useState<DashboardState>({
    tutorMetrics: [],
    alerts: [],
    interventionTasks: [],
    analytics: null,
    connected: false,
    lastUpdate: null,
  });

  const wsServiceRef = useRef(getWebSocketService(WS_URL));

  const handleMessage = useCallback((message: WebSocketMessage) => {
    setState((prevState) => {
      const newState = { ...prevState, lastUpdate: message.timestamp };

      switch (message.type) {
        case 'metrics_update':
          const metricsData = message.data as any;
          const existingIndex = newState.tutorMetrics.findIndex(
            (m) => m.tutor_id === metricsData.tutor_id && m.window === metricsData.window
          );

          if (existingIndex >= 0) {
            newState.tutorMetrics[existingIndex] = metricsData;
          } else {
            newState.tutorMetrics.push(metricsData);
          }
          break;

        case 'alert':
          const alertData = message.data as any;
          const alertExists = newState.alerts.some((a) => a.id === alertData.id);

          if (!alertExists) {
            newState.alerts = [alertData, ...newState.alerts];
          }
          break;

        case 'intervention':
          const interventionData = message.data as any;
          const interventionIndex = newState.interventionTasks.findIndex(
            (t) => t.id === interventionData.id
          );

          if (interventionIndex >= 0) {
            newState.interventionTasks[interventionIndex] = interventionData;
          } else {
            newState.interventionTasks.push(interventionData);
          }
          break;

        case 'analytics_update':
          const analyticsData = message.data as any;

          // Handle connection status updates
          if ('connected' in analyticsData) {
            newState.connected = analyticsData.connected;
          } else {
            newState.analytics = analyticsData;
          }
          break;

        default:
          console.warn('Unknown message type:', message.type);
      }

      return newState;
    });
  }, []);

  useEffect(() => {
    const wsService = wsServiceRef.current;

    // Subscribe to messages
    const unsubscribe = wsService.subscribe(handleMessage);

    // Connect to WebSocket
    wsService.connect();

    // Cleanup on unmount
    return () => {
      unsubscribe();
      wsService.disconnect();
    };
  }, [handleMessage]);

  const resolveAlert = useCallback((alertId: string) => {
    setState((prevState) => ({
      ...prevState,
      alerts: prevState.alerts.map((alert) =>
        alert.id === alertId ? { ...alert, resolved: true } : alert
      ),
    }));
  }, []);

  const updateInterventionStatus = useCallback(
    (taskId: string, status: 'pending' | 'in_progress' | 'completed') => {
      setState((prevState) => ({
        ...prevState,
        interventionTasks: prevState.interventionTasks.map((task) =>
          task.id === taskId ? { ...task, status } : task
        ),
      }));
    },
    []
  );

  return {
    state,
    resolveAlert,
    updateInterventionStatus,
  };
}
