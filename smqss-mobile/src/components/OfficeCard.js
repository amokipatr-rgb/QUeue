import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';

export default function OfficeCard({ office }) {
  const isAvailable = (office.availability_status || '').toLowerCase() === 'available';
  return (
    <View style={[styles.card, !isUnavailable && styles.cardDimmed]}>
      <View style={styles.top}>
        <Text style={styles.name} numberOfLines={1}>{office.office_name}</Text>
        <Text style={styles.location} numberOfLines={1}>{office.location}</Text>
      </View>
      <View style={styles.bottom}>
        <View style={[styles.badge, isAvailable ? styles.badgeAvailable : styles.badgeClosed]}>
          <View style={[styles.dot, isAvailable ? styles.dotGreen : styles.dotGold]} />
          <Text style={[styles.badgeText, isAvailable ? styles.badgeTextGreen : styles.badgeTextGold]}>
            {isAvailable ? 'Available' : 'CLOSED'}
          </Text>
        </View>
        {isAvailable && (
          <Text style={styles.waiting}>{office.waiting_count || 0} waiting</Text>
        )}
      </View>
    </View>
  );
}

const isUnavailable = false;

const styles = StyleSheet.create({
  card: {
    width: '48%',
    backgroundColor: COLORS.officeCard,
    borderRadius: SIZES.chipRadius,
    padding: 14,
    borderWidth: 1,
    borderColor: 'rgba(255,255,255,0.06)',
  },
  cardDimmed: { opacity: 0.6 },
  top: { marginBottom: 10 },
  name: {
    fontFamily: FONTS.dmSans,
    fontSize: 14,
    fontWeight: '600',
    color: COLORS.textBright,
    marginBottom: 2,
  },
  location: {
    fontFamily: FONTS.dmSans,
    fontSize: 11,
    color: COLORS.textMuted,
  },
  bottom: { flexDirection: 'row', alignItems: 'center', justifyContent: 'space-between' },
  badge: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 4,
    paddingHorizontal: 8,
    paddingVertical: 3,
    borderRadius: 10,
  },
  badgeAvailable: { backgroundColor: 'rgba(0,230,118,0.12)' },
  badgeClosed: { backgroundColor: 'rgba(232,197,71,0.12)' },
  dot: { width: 6, height: 6, borderRadius: 3 },
  dotGreen: { backgroundColor: COLORS.green },
  dotGold: { backgroundColor: COLORS.gold },
  badgeText: { fontFamily: FONTS.dmMono, fontSize: 10, fontWeight: '500' },
  badgeTextGreen: { color: COLORS.green },
  badgeTextGold: { color: COLORS.gold },
  waiting: {
    fontFamily: FONTS.dmMono,
    fontSize: 11,
    color: COLORS.textMuted,
  },
});
