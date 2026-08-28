import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { COLORS, FONTS } from '../theme/colors';

export default function RecallBanner({ recall }) {
  const scaleAnim = useRef(new Animated.Value(0)).current;
  const opacityAnim = useRef(new Animated.Value(0)).current;
  const prevId = useRef(null);

  useEffect(() => {
    if (!recall || recall.id === prevId.current) return;
    prevId.current = recall.id;
    scaleAnim.setValue(0);
    opacityAnim.setValue(0);

    Animated.sequence([
      Animated.parallel([
        Animated.spring(scaleAnim, { toValue: 1, friction: 6, tension: 40, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 1, duration: 300, useNativeDriver: true }),
      ]),
      Animated.delay(2000),
      Animated.parallel([
        Animated.timing(scaleAnim, { toValue: 0.8, duration: 300, useNativeDriver: true }),
        Animated.timing(opacityAnim, { toValue: 0, duration: 300, useNativeDriver: true }),
      ]),
    ]).start();
  }, [recall?.id]);

  if (!recall) return null;

  const label = recall.student_name
    ? `${recall.student_name} — ${recall.token_number}`
    : `${recall.token_number} — ${recall.office_name || ''}`;

  return (
    <Animated.View
      style={[
        styles.banner,
        { transform: [{ scale: scaleAnim }], opacity: opacityAnim },
      ]}
    >
      <Text style={styles.text} numberOfLines={1}>{label}</Text>
    </Animated.View>
  );
}

const styles = StyleSheet.create({
  banner: {
    position: 'absolute',
    top: '40%',
    alignSelf: 'center',
    backgroundColor: COLORS.red,
    borderRadius: 30,
    paddingHorizontal: 24,
    paddingVertical: 14,
    zIndex: 300,
    elevation: 300,
    shadowColor: '#ff6d00',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.5,
    shadowRadius: 20,
  },
  text: {
    fontFamily: FONTS.dmMono,
    fontSize: 18,
    fontWeight: '500',
    color: COLORS.white,
    letterSpacing: 1,
  },
});
