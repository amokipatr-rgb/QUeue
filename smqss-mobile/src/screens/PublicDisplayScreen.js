import React, { useEffect, useState, useRef } from 'react';
import { View, Text, StyleSheet, ScrollView, StatusBar } from 'react-native';
import { COLORS, FONTS, SIZES } from '../theme/colors';
import Header from '../components/Header';
import ActiveTokenCard from '../components/ActiveTokenCard';
import IdleState from '../components/IdleState';
import NoticesSection from '../components/NoticesSection';
import StatsBar from '../components/StatsBar';
import NewsTicker from '../components/NewsTicker';
import RecallBanner from '../components/RecallBanner';
import VoiceIndicator from '../components/VoiceIndicator';
import { OfflineBanner, OnlineBanner } from '../components/Banners';
import useQueueData from '../hooks/useQueueData';
import useNetworkStatus from '../hooks/useNetworkStatus';
import { syncServerTime } from '../services/time';

export default function PublicDisplayScreen() {
  const { queues, upNext, recalls, messages, isIdle, stats, activeTokens, allNotices } = useQueueData();
  const { isConnected, showOnline } = useNetworkStatus();
  const [voiceStatus, setVoiceStatus] = useState('Voice SMQSS Ready');

  useEffect(() => {
    syncServerTime();
    const timer = setInterval(syncServerTime, 300000);
    return () => clearInterval(timer);
  }, []);

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor={COLORS.bg} />
      <Header />
      <ScrollView style={styles.scroll} contentContainerStyle={styles.scrollContent}>
        {isIdle ? (
          <IdleState queues={queues} />
        ) : (
          <ActiveTokenCard tokens={activeTokens} />
        )}
        <NoticesSection notices={allNotices} upNext={upNext} isIdle={isIdle} />
        <StatsBar stats={stats} activeTokens={activeTokens} isIdle={isIdle} />
      </ScrollView>
      <NewsTicker notices={allNotices} isIdle={isIdle} />
      <View style={styles.footer}>
        <Text style={styles.footerText}>Listen for your token announcement</Text>
        <Text style={styles.footerDot}>•</Text>
        <Text style={styles.footerText}>Watch the screen for your turn</Text>
        <Text style={styles.footerDot}>•</Text>
        <Text style={styles.footerText}>SMQSS — Enhancing Student Service</Text>
      </View>
      <RecallBanner recall={recalls && recalls.length > 0 ? recalls[0] : null} />
      <VoiceIndicator status={voiceStatus} />
      <OfflineBanner visible={!isConnected} />
      <OnlineBanner visible={showOnline} />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: COLORS.bg,
  },
  scroll: {
    flex: 1,
  },
  scrollContent: {
    paddingTop: SIZES.headerHeight + 8,
    paddingBottom: SIZES.tickerHeight + SIZES.footerHeight + 20,
  },
  footer: {
    height: SIZES.footerHeight,
    backgroundColor: COLORS.headerBg,
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'center',
    gap: 8,
    borderTopWidth: 1,
    borderTopColor: 'rgba(232,197,71,0.1)',
  },
  footerText: {
    fontFamily: FONTS.dmSans,
    fontSize: 10,
    color: COLORS.textMuted,
  },
  footerDot: {
    color: COLORS.goldDark,
    fontSize: 8,
  },
});
