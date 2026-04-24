import 'react-native-reanimated';
import 'react-native-gesture-handler';
import { ClerkProvider, useAuth, useUser } from '@clerk/expo'
import { tokenCache } from '@clerk/expo/token-cache'
import { Stack, useRouter, usePathname } from 'expo-router'
import { useColorScheme, View, Text, StyleSheet } from 'react-native'
import { GestureHandlerRootView } from 'react-native-gesture-handler'
import { StatusBar } from 'expo-status-bar';
import { useEffect } from 'react';
import { LinearGradient } from 'expo-linear-gradient';
import { syncUser } from '../utils/api';

import '../global.css'

const publishableKey = process.env.EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY || '';

if (!publishableKey) {
  console.warn('Missing Clerk Publishable Key mapping. Check your .env file.');
}

export default function RootLayout() {
  const colorScheme = useColorScheme()

  if (!publishableKey) {
    return (
      <View style={{ flex: 1, alignItems: 'center', justifyContent: 'center', backgroundColor: '#0F172A' }}>
        <Text style={{ color: '#F1F5F9', fontSize: 16, fontWeight: '600' }}>
          Missing Clerk publishable key
        </Text>
        <Text style={{ color: '#94A3B8', marginTop: 8 }}>
          Set `EXPO_PUBLIC_CLERK_PUBLISHABLE_KEY` in `.env` and restart Expo.
        </Text>
      </View>
    );
  }

  return (
    <GestureHandlerRootView style={{ flex: 1 }}>
      <ClerkProvider publishableKey={publishableKey} tokenCache={tokenCache}>
        <AppContent />
      </ClerkProvider>
    </GestureHandlerRootView>
  )
}

function AppContent() {
  const colorScheme = useColorScheme();
  const router = useRouter();
  const { isLoaded, isSignedIn, getToken } = useAuth();
  const { user } = useUser();
  const pathname = usePathname();

  useEffect(() => {
    if (!isLoaded || !isSignedIn || !user) {
      return;
    }

    const sync = async () => {
      try {
        const token = await getToken();
        if (token) {
          const response = await syncUser(token, {
            clerkId: user.id,
            email: user.primaryEmailAddress?.emailAddress,
            firstName: user.firstName || undefined,
            lastName: user.lastName || undefined,
            username: user.username || undefined,
          });
          console.log('User synced on app launch/auth change');
          
          if (response?.needsOnboarding && pathname !== '/complete-profile') {
            router.replace('/complete-profile');
          }
        }
      } catch (error) {
        console.error('Failed to sync user on launch:', error);
      }
    };

    sync();
  }, [getToken, isLoaded, isSignedIn, user]);

  return (
    <View style={styles.container}>
      <LinearGradient
        colors={colorScheme === 'dark'
          ? ['#0f0c29', '#302b63', '#24243e'] 
          : ['#E0F2FE', '#F0F9FF', '#FFF7ED']
        }
        style={styles.background}
      />
      <Stack
        screenOptions={{
          headerShown: false,
          contentStyle: { backgroundColor: 'transparent' },
          animation: 'fade',
        }}
      >
        <Stack.Screen name="(auth)" />
        <Stack.Screen name="(home)" />
        <Stack.Screen name="transactions/add" options={{ presentation: 'modal' }} />
        <Stack.Screen name="accounts/index" />
        <Stack.Screen name="accounts/add" options={{ presentation: 'modal' }} />
        <Stack.Screen name="categories/index" />
        <Stack.Screen name="categories/add" options={{ presentation: 'modal' }} />
        <Stack.Screen name="budgets/add" options={{ presentation: 'modal' }} />
      </Stack>
      <StatusBar style="light" />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
  background: {
    ...StyleSheet.absoluteFillObject,
  },
});
