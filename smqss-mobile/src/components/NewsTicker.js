import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';
import { getEATShortTime } from '../services/time';

const STANDBY = [
  '📱 Download SMQSS app to check queue status from your phone',
  '📋 Please have your Student ID ready before taking a token',
  '⏱ Average wait time: 5-10 minutes per token',
];

export default function NewsTicker({ notices, isIdle }) {
  const scrollX = useRef(new Animated.Value(0)).current;

  useEffect(() => {
    if (!isIdle) return;
    const anim = Animated.loop(
      Animated.timing(scrollX, { toValue: -1200, duration: 28000, useNativeDriver: true })
    );
    anim.start();
    return () => anim.stop();
  }, [isIdle]);

  if (!isIdle) return null;

  const items = notices && notices.length > 0
    ? notices.map((n) => `From: ${n.office_name || 'Office'} — ${n.message || ''}`)
    : STANDBY;

  const tickerText = items.join('   ◆   ');

  return (
    <View style={styles.wrap}>
      <View style={styles.topBar} />
      <View style={styles.body}>
        <View style={styles.labelWrap}>
          <View style={styles.labelDot} />
          <Text style={styles.labelText}>NOTICE</Text>
        </View>
        <View style={styles.track}>
          <Animated.View style={[styles.scrollInner, { transform: [{ translateX: scrollX }] }]}>
            <Text style={styles.scrollText}>{tickerText}   ◆   {tickerText}</Text>
          </Animated.View>
        </View>
        <Text style={styles.time}>{getEATShortTime()}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  wrap: { height: SIZES.tickerHeight },
  topBar: {
    height: 3,
    backgroundColor: COLORS.goldDark,
  },
  body: {
    flex: 1,
    flexDirection: 'row',
    alignItems: 'center',
    backgroundColor: 'rgba(7,13,9,0.95)',
    paddingHorizontal: 12,
  },
  labelWrap: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    backgroundColor: COLORS.goldDark,
    paddingHorizontal: 10,
    paddingVertical: 4,
    borderRadius: 4,
    marginRight: 10,
  },
  labelDot: {
    width: 6,
    height: 6,
    borderRadius: 3,
    backgroundColor: COLORS.gold,
  },
  labelText: {
    fontFamily: FONTS.dmMono,
    fontSize: 10,
    fontWeight: '500',
    color: COLORS.white,
    textTransform: 'uppercase',
    letterSpacing: 1,
  },
  track: { flex: 1, overflow: 'hidden' },
  scrollInner: { flexDirection: 'row' },
  scrollText: {
    fontFamily: FONTS.dmSans,
    fontSize: 12,
    color: COLORS.text,
    whiteSpace: 'nowrap',
  },
  time: {
    fontFamily: FONTS.dmMono,
    fontSize: 11,
    color: COLORS.textMuted,
    marginLeft: 10,
  },
});
