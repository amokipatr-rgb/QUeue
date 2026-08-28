import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';
import OfficeCard from './OfficeCard';

export default function IdleState({ queues }) {
  const hasOffices = queues && queues.length > 0;
  return (
    <View style={styles.container}>
      <Text style={styles.title}>No Active Services</Text>
      <Text style={styles.sub}>Please take a token from the kiosk</Text>
      <Text style={styles.goldText}>Permission to sit for Exam is Granted by VC</Text>
      <View style={styles.kioskPill}>
        <View style={styles.kioskDot} />
        <Text style={styles.kioskText}>Kiosk available at the entrance</Text>
      </View>
      {hasOffices && (
        <View style={styles.officesSection}>
          <View style={styles.officesHeader}>
            <View style={styles.officesDot} />
            <Text style={styles.officesTitle}>Service Offices</Text>
          </View>
          <View style={styles.officesGrid}>
            {queues.map((office, i) => (
              <OfficeCard key={i} office={office} />
            ))}
          </View>
          {queues.every((o) => (o.availability_status || '').toLowerCase() !== 'available') && (
            <Text style={styles.closedText}>All offices are currently closed.</Text>
          )}
        </View>
      )}
    </View>
  );
}

const styles = StyleSheet.create({
  container: { alignItems: 'center', padding: 24 },
  title: {
    fontFamily: FONTS.playfair,
    fontSize: 28,
    fontWeight: '700',
    color: COLORS.textBright,
    marginBottom: 8,
  },
  sub: {
    fontFamily: FONTS.dmSans,
    fontSize: 15,
    color: COLORS.textMuted,
    marginBottom: 16,
  },
  goldText: {
    fontFamily: FONTS.dmSans,
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gold,
    letterSpacing: 0.3,
    marginBottom: 16,
  },
  kioskPill: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: 'rgba(232,197,71,0.08)',
    borderWidth: 1,
    borderColor: 'rgba(232,197,71,0.2)',
    borderRadius: 20,
    paddingHorizontal: 16,
    paddingVertical: 8,
  },
  kioskDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.gold,
  },
  kioskText: {
    fontFamily: FONTS.dmSans,
    fontSize: 12,
    color: COLORS.text,
  },
  officesSection: { width: '100%', marginTop: 24 },
  officesHeader: { flexDirection: 'row', alignItems: 'center', gap: 8, marginBottom: 12 },
  officesDot: {
    width: 8,
    height: 8,
    borderRadius: 4,
    backgroundColor: COLORS.gold,
  },
  officesTitle: {
    fontFamily: FONTS.dmMono,
    fontSize: 13,
    fontWeight: '500',
    color: COLORS.gold,
    textTransform: 'uppercase',
    letterSpacing: 2,
  },
  officesGrid: { flexDirection: 'row', flexWrap: 'wrap', gap: 10 },
  closedText: {
    fontFamily: FONTS.dmSans,
    fontSize: 13,
    color: COLORS.textMuted,
    textAlign: 'center',
    marginTop: 16,
  },
});
