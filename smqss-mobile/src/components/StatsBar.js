import React from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';

export default function StatsBar({ stats, activeTokens, isIdle }) {
  return (
    <View style={styles.bar}>
      <View style={styles.chip}>
        <View style={[styles.iconWrap, styles.iconWaiting]}>
          <Text style={styles.iconText}>⏱</Text>
        </View>
        <View>
          <Text style={styles.statVal}>{stats.totalWaiting}</Text>
          <Text style={styles.statLbl}>Waiting</Text>
        </View>
      </View>
      <View style={styles.chip}>
        <View style={[styles.iconWrap, styles.iconCalled]}>
          <Text style={styles.iconText}>📞</Text>
        </View>
        <View>
          <Text style={styles.statVal}>
            {isIdle ? stats.totalCalled : Math.min(stats.totalCalled, 8)}
            {!isIdle && stats.totalCalled > 8 ? '+' : ''}
          </Text>
          <Text style={styles.statLbl}>{isIdle ? 'Called' : 'Up Next'}</Text>
        </View>
      </View>
      <View style={styles.chip}>
        <View style={[styles.iconWrap, styles.iconServing]}>
          <Text style={styles.iconText}>▶</Text>
        </View>
        <View>
          <Text style={styles.statVal}>{stats.totalServing}</Text>
          <Text style={styles.statLbl}>Serving Now</Text>
        </View>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  bar: {
    flexDirection: 'row',
    justifyContent: 'center',
    gap: 12,
    padding: 12,
  },
  chip: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 8,
    backgroundColor: COLORS.statChip,
    borderRadius: SIZES.chipRadius,
    paddingHorizontal: 14,
    paddingVertical: 10,
  },
  iconWrap: {
    width: 32,
    height: 32,
    borderRadius: 16,
    alignItems: 'center',
    justifyContent: 'center',
  },
  iconWaiting: { backgroundColor: 'rgba(255,152,0,0.12)' },
  iconCalled: { backgroundColor: 'rgba(232,197,71,0.12)' },
  iconServing: { backgroundColor: 'rgba(0,230,118,0.12)' },
  iconText: { fontSize: 14 },
  statVal: {
    fontFamily: FONTS.dmMono,
    fontSize: 16,
    fontWeight: '500',
    color: COLORS.textBright,
  },
  statLbl: {
    fontFamily: FONTS.dmSans,
    fontSize: 10,
    color: COLORS.textMuted,
  },
});
