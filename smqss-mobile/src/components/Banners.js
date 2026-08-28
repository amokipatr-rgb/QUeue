import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { COLORS, FONTS } from '../theme/colors';

export function OfflineBanner({ visible }) {
  const translateY = useRef(new Animated.Value(100)).current;

  useEffect(() => {
    Animated.spring(translateY, {
      toValue: visible ? 0 : 100,
      tension: 50,
      friction: 8,
      useNativeDriver: true,
    }).start();
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.banner, styles.offline, { transform: [{ translateY }] }]}>
      <Text style={styles.icon}>📡</Text>
      <Text style={styles.text}>No internet connection, reconnecting...</Text>
    </Animated.View>
  );
}

export function OnlineBanner({ visible }) {
  const translateY = useRef(new Animated.Value(100)).current;

  useEffect(() => {
    Animated.spring(translateY, {
      toValue: visible ? 0 : 100,
      tension: 50,
      friction: 8,
      useNativeDriver: true,
    }).start();
  }, [visible]);

  if (!visible) return null;

  return (
    <Animated.View style={[styles.banner, styles.online, { transform: [{ translateY }] }]}>
      <Text style={styles.icon}>✓</Text>
      <Text style={styles.text}>SMQSS Back Online</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  banner: {
    position: 'absolute',
    bottom: 0,
    left: 0,
    right: 0,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    paddingVertical: 14,
    paddingHorizontal: 24,
    zIndex: 9999,
    elevation: 9999,
  },
  offline: { backgroundColor: 'rgba(230,81,0,0.92)' },
  online: { backgroundColor: 'rgba(34,197,94,0.92)' },
  icon: { fontSize: 18 },
  text: {
    fontFamily: FONTS.dmSans,
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.white,
  },
});
