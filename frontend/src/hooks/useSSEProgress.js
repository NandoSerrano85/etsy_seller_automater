import { useState, useEffect, useCallback, useRef } from 'react';
import { useApi } from './useApi';

export const useSSEProgress = () => {
  const api = useApi();
  const [sessionId, setSessionId] = useState(null);
  const [progress, setProgress] = useState({
    step: 0,
    totalSteps: 4,
    message: '',
    progressPercent: 0,
    elapsedTime: 0,
  });
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const eventSourceRef = useRef(null);

  const startProgressSession = useCallback(async () => {
    try {
      const response = await api.post('/designs/start-upload', {});
      const newSessionId = response.session_id;
      setSessionId(newSessionId);
      console.log('🚀 Started upload session:', newSessionId);
      return newSessionId;
    } catch (err) {
      console.error('❌ Failed to start upload session:', err);
      setError(err.message);
      throw err;
    }
  }, [api]);

  const connectToProgressStream = useCallback(sessionId => {
    if (!sessionId) return;

    // Close existing connection
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const token = localStorage.getItem('token') || sessionStorage.getItem('token');
    if (!token) {
      setError('No authentication token found');
      return;
    }

    // Create EventSource with auth token in URL params (since EventSource doesn't support custom headers)
    const baseUrl = process.env.REACT_APP_API_BASE_URL || 'http://localhost:3003';
    const url = `${baseUrl}/designs/progress/${sessionId}?token=${encodeURIComponent(token)}`;

    console.log('🔗 Connecting to SSE stream:', url);

    const eventSource = new EventSource(url);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('✅ SSE connection opened');
      setIsConnected(true);
      setError(null);
    };

    eventSource.onmessage = event => {
      try {
        const data = JSON.parse(event.data);
        console.log('📡 SSE progress update:', data);

        if (data.type === 'keepalive') {
          // Ignore keepalive messages
          return;
        }

        setProgress({
          step: data.step || 0,
          totalSteps: data.total_steps || 4,
          message: data.message || '',
          progressPercent: data.progress_percent || 0,
          elapsedTime: data.elapsed_time || 0,
        });

        // If upload is complete, close the connection after a delay
        if (data.step === data.total_steps) {
          setTimeout(() => {
            eventSource.close();
            setIsConnected(false);
          }, 2000);
        }
      } catch (err) {
        console.error('❌ Error parsing SSE data:', err);
      }
    };

    eventSource.onerror = event => {
      console.error('❌ SSE connection error:', event);
      setError('Connection to progress stream failed');
      setIsConnected(false);
      eventSource.close();
    };
  }, []);

  const disconnectFromProgressStream = useCallback(() => {
    if (eventSourceRef.current) {
      console.log('🔌 Disconnecting from SSE stream');
      eventSourceRef.current.close();
      eventSourceRef.current = null;
      setIsConnected(false);
    }
  }, []);

  const resetProgress = useCallback(() => {
    setProgress({
      step: 0,
      totalSteps: 4,
      message: '',
      progressPercent: 0,
      elapsedTime: 0,
    });
    setError(null);
    setSessionId(null);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      disconnectFromProgressStream();
    };
  }, [disconnectFromProgressStream]);

  return {
    sessionId,
    progress,
    isConnected,
    error,
    startProgressSession,
    connectToProgressStream,
    disconnectFromProgressStream,
    resetProgress,
  };
};
