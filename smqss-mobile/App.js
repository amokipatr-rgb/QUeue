import React from 'react';
import { ActivityIndicator, View, StyleSheet } from 'react-native';
import { useFonts, PlayfairDisplay_700Bold, PlayfairDisplay_900Black } from '@expo-google-fonts/playfair-display';
import { DMSans_400Regular, DMSans_500Medium, DMSans_600SemiBold } from '@expo-google-fonts/dm-sans';
import { DMMono_400Regular, DMMono_500Medium } from '@expo-google-fonts/dm-mono';
import PublicDisplayScreen from './src/screens/PublicDisplayScreen';

export default function App() {
  const [fontsLoaded] = useFonts({
    PlayfairDisplay_700Bold,
    PlayfairDisplay_900Black,
    DMSans_400Regular,
    DMSans_500Medium,
    DMSans_600SemiBold,
    DMMono_400Regular,
    DMMono_500Medium,
  });

  if (!fontsLoaded) {
    return (
      <View style={styles.loading}>
        <ActivityIndicator size="large" color="#e8c547" />
      </View>
    );
  }

  return <PublicDisplayScreen />;
}

const styles = StyleSheet.create({
  loading: {
    flex: 1,
    backgroundColor: '#070d09',
    alignItems: 'center',
    justifyContent: 'center',
  },
});
