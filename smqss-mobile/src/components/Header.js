import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';
import { getEATTime, getEATDate } from '../services/time';

export default function Header() {
  const [time, setTime] = useState(getEATTime());
  const [date, setDate] = useState(getEATDate());

  useEffect(() => {
    const timer = setInterval(() => {
      setTime(getEATTime());
      setDate(getEATDate());
    }, 1000);
    return () => clearInterval(timer);
  }, []);

  return (
    <View style={styles.header}>
      <View style={styles.left}>
        <View style={styles.logoWrap}>
          <Text style={styles.logoStar}>★</Text>
        </View>
        <View>
          <Text style={styles.brand}>SMQSS</Text>
          <Text style={styles.sub}>Queue Management System</Text>
        </View>
      </View>
      <View style={styles.center}>
        <Text style={styles.hcTitle}>Makerere University</Text>
        <Text style={styles.hcSub}>Student Service Board</Text>
      </View>
      <View style={styles.right}>
        <Text style={styles.time}>{time}</Text>
        <Text style={styles.date}>{date}</Text>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  header: {
    height: SIZES.headerHeight,
    backgroundColor: COLORS.headerBg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    paddingHorizontal: 20,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(232,197,71,0.15)',
  },
  left: { flexDirection: 'row', alignItems: 'center', gap: 10 },
  logoWrap: {
    width: 40,
    height: 40,
    borderRadius: 20,
    backgroundColor: 'rgba(232,197,71,0.12)',
    alignItems: 'center',
    justifyContent: 'center',
    borderWidth: 1.5,
    borderColor: 'rgba(232,197,71,0.3)',
  },
  logoStar: { color: COLORS.gold, fontSize: 18 },
  brand: {
    fontFamily: FONTS.dmMonoMedium,
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.gold,
    letterSpacing: 1,
  },
  sub: {
    fontFamily: FONTS.dmSans,
    fontSize: 9,
    color: COLORS.textMuted,
    letterSpacing: 0.5,
    textTransform: 'uppercase',
  },
  center: { alignItems: 'center' },
  hcTitle: {
    fontFamily: FONTS.playfair,
    fontSize: 16,
    fontWeight: '700',
    color: COLORS.textBright,
  },
  hcSub: {
    fontFamily: FONTS.dmSans,
    fontSize: 10,
    color: COLORS.textMuted,
    textTransform: 'uppercase',
    letterSpacing: 2,
  },
  right: { alignItems: 'flex-end' },
  time: {
    fontFamily: FONTS.dmMono,
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gold,
  },
  date: {
    fontFamily: FONTS.dmSans,
    fontSize: 10,
    color: COLORS.textMuted,
  },
});
