import React, { useEffect, useRef } from 'react';
import { View, Text, StyleSheet, Animated } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';

function TokenCard({ token, type }) {
  const pulseAnim = useRef(new Animated.Value(1)).current;
  const isServing = type === 'serving';

  useEffect(() => {
    const anim = Animated.loop(
      Animated.sequence([
        Animated.timing(pulseAnim, { toValue: isServing ? 0.7 : 0.5, duration: isServing ? 700 : 1000, useNativeDriver: true }),
        Animated.timing(pulseAnim, { toValue: 1, duration: isServing ? 700 : 1000, useNativeDriver: true }),
      ])
    );
    anim.start();
    return () => anim.stop();
  }, []);

  const tokens = token.token_number || '';
  const names = token.student_name || 'Student';

  return (
    <Animated.View
      style={[
        styles.card,
        isServing ? styles.cardServing : styles.cardCalled,
        { opacity: pulseAnim },
      ]}
    >
      <View style={[styles.badge, isServing ? styles.badgeServing : styles.badgeCalled]}>
        <View style={[styles.badgeDot, isServing ? styles.dotGreen : styles.dotAmber]} />
        <Text style={[styles.badgeText, isServing ? styles.badgeTextGreen : styles.badgeTextAmber]}>
          {isServing ? 'BEING SERVED NOW' : 'CALLED — PLEASE PROCEED'}
        </Text>
      </View>
      <Text style={[styles.tokenNumber, isServing ? styles.tokenGreen : styles.tokenAmber]}>
        {tokens}
      </Text>
      <Text style={styles.studentName}>{names}</Text>
      <Text style={styles.officeName}>{token.office_name}</Text>
    </Animated.View>
  );
}

export default function ActiveTokenCard({ tokens }) {
  if (!tokens || !tokens.length) return null;
  return (
    <View style={styles.grid}>
      {tokens.map((t, i) => (
        <TokenCard key={`${t.token_number}-${i}`} token={t} type={t.type} />
      ))}
    </View>
  );
}

const styles = StyleSheet.create({
  grid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
    padding: 16,
  },
  card: {
    width: '100%',
    borderRadius: SIZES.cardRadius,
    padding: 20,
    borderWidth: 2,
  },
  cardCalled: {
    backgroundColor: COLORS.cardCalled,
    borderColor: COLORS.cardCalledBorder,
  },
  cardServing: {
    backgroundColor: COLORS.cardServing,
    borderColor: COLORS.cardServingBorder,
  },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 6,
    marginBottom: 12,
    alignSelf: 'flex-start',
    paddingHorizontal: 12,
    paddingVertical: 6,
    borderRadius: 20,
  },
  badgeCalled: { backgroundColor: 'rgba(255,152,0,0.15)' },
  badgeServing: { backgroundColor: 'rgba(0,230,118,0.15)' },
  badgeDot: { width: 8, height: 8, borderRadius: 4 },
  dotGreen: { backgroundColor: COLORS.green },
  dotAmber: { backgroundColor: COLORS.amber },
  badgeText: { fontFamily: FONTS.dmMono, fontSize: 10, fontWeight: '500', letterSpacing: 1 },
  badgeTextAmber: { color: COLORS.amberLight },
  badgeTextGreen: { color: COLORS.greenLight },
  tokenNumber: {
    fontFamily: FONTS.dmMono,
    fontSize: 48,
    fontWeight: '500',
    letterSpacing: 4,
    marginBottom: 8,
  },
  tokenAmber: { color: COLORS.amberLight },
  tokenGreen: { color: COLORS.greenLight },
  studentName: {
    fontFamily: FONTS.dmSans,
    fontSize: 16,
    color: COLORS.text,
    marginBottom: 4,
  },
  officeName: {
    fontFamily: FONTS.dmSans,
    fontSize: 13,
    color: COLORS.textMuted,
  },
});
