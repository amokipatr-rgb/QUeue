import { useState, useEffect, useRef } from 'react';
import NetInfo from '@react-native-community/netinfo';

export default function useNetworkStatus() {
  const [isConnected, setIsConnected] = useState(true);
  const [showOnline, setShowOnline] = useState(false);
  const failedFetches = useRef(0);

  useEffect(() => {
    const unsub = NetInfo.addEventListener((state) => {
      const connected = state.isConnected && state.isInternetReachable !== false;
      if (connected && !isConnected) {
        setShowOnline(true);
        setTimeout(() => setShowOnline(false), 3000);
        failedFetches.current = 0;
      }
      setIsConnected(connected);
    });
    return () => unsub();
  }, [isConnected]);

  return { isConnected, showOnline, offline: !isConnected };
}
