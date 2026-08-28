import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';

export default function NoticesSection({ notices, upNext, isIdle }) {
  const [index, setIndex] = useState(0);

  useEffect(() => {
    if (!notices || notices.length <= 1) return;
    const timer = setInterval(() => {
      setIndex((prev) => (prev + 1) % notices.length);
    }, 7000);
    return () => clearInterval(timer);
  }, [notices?.length]);

  if (!isIdle) return null;
  const hasNotices = notices && notices.length > 0;
  const hasUpNext = upNext && upNext.length > 0;
  if (!hasNotices && !hasUpNext) return null;

  const title = hasNotices && hasUpNext ? 'Notices & Up Next'
    : hasNotices ? 'Notices' : 'Up Next';

  return (
    <View style={styles.container}>
      <View style={styles.headerRow}>
        <View style={styles.dot} />
        <Text style={styles.title}>{title}</Text>
        <View style={styles.dot} />
      </View>
      <View style={styles.content}>
        {hasNotices && (
          <View style={styles.noticeCard}>
            <Text style={styles.noticeLabel}>
              Notice From: <Text style={styles.noticeOffice}>{notices[index % notices.length]?.office_name || 'Office Notice'}</Text>
            </Text>
            <Text style={styles.noticeText}>{notices[index % notices.length]?.message || ''}</Text>
          </View>
        )}
        {hasUpNext && (
          <View style={styles.upNextCard}>
            {upNext.slice(0, 10).map((t, i) => (
              <View key={i} style={[styles.upNextRow, i === 0 && styles.upNextRowFirst]}>
                <Text style={styles.upNextToken}>{t.token_number}</Text>
                {t.student_name ? <Text style={styles.upNextName}>{t.student_name}</Text> : null}
              </View>
            ))}
          </View>
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: { padding: 16 },
  headerRow: {
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 10,
    marginBottom: 12,
  },
  dot: { width: 6, height: 6, borderRadius: 3, backgroundColor: COLORS.gold, opacity: 0.5 },
  title: {
    fontFamily: FONTS.dmMono,
    fontSize: 13,
    fontWeight: '900',
    color: COLORS.white,
    textTransform: 'uppercase',
    letterSpacing: 2.5,
  },
  content: { gap: 10 },
  noticeCard: {
    backgroundColor: COLORS.noticeCard,
    borderWidth: 1,
    borderColor: COLORS.noticeCardBorder,
    borderRadius: 12,
    padding: 14,
  },
  noticeLabel: {
    fontFamily: FONTS.dmSans,
    fontSize: 13,
    fontWeight: '700',
    color: COLORS.gold,
    marginBottom: 4,
  },
  noticeOffice: { color: COLORS.greenLight },
  noticeText: {
    fontFamily: FONTS.dmSans,
    fontSize: 13,
    color: COLORS.text,
    lineHeight: 18,
  },
  upNextCard: {
    backgroundColor: COLORS.noticeCard,
    borderWidth: 1,
    borderColor: COLORS.noticeCardBorder,
    borderRadius: 12,
    padding: 10,
  },
  upNextRow: {
    flexDirection: 'row',
    alignItems: 'center',
    gap: 10,
    paddingVertical: 6,
    paddingHorizontal: 8,
    borderBottomWidth: 1,
    borderBottomColor: 'rgba(255,255,255,0.04)',
  },
  upNextRowFirst: {
    borderLeftWidth: 3,
    borderLeftColor: COLORS.gold,
    backgroundColor: 'rgba(232,197,71,0.06)',
  },
  upNextToken: {
    fontFamily: FONTS.dmMono,
    fontSize: 14,
    fontWeight: '500',
    color: COLORS.gold,
    minWidth: 60,
  },
  upNextName: {
    fontFamily: FONTS.dmSans,
    fontSize: 13,
    color: COLORS.greenLight,
  },
});
