import React, { useState, useEffect } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { Banknote, CreditCard, Landmark, Wallet, X, Trash2 } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';

import { NeonButton } from '../../components/NeonButton';
import { NeonInput } from '../../components/NeonInput';
import { useApi } from '../../hooks/useApi';
import { AccountType, useStore } from '../../store/useStore';

const ACCOUNT_TYPES: { key: AccountType; label: string; icon: React.ReactNode }[] = [
  { key: 'cash', label: 'Cash', icon: <Banknote size={18} color="#94A3B8" /> },
  { key: 'bank', label: 'Bank', icon: <Landmark size={18} color="#38BDF8" /> },
  { key: 'card', label: 'Card', icon: <CreditCard size={18} color="#F59E0B" /> },
  { key: 'wallet', label: 'Wallet', icon: <Wallet size={18} color="#10B981" /> },
];

export default function EditAccount() {
  const { id } = useLocalSearchParams();
  const api = useApi();
  const { accounts, setAccounts, setDashboardSummary } = useStore();

  const account = accounts.find((a) => a.id === id);

  const [name, setName] = useState(account?.name || '');
  const [balance, setBalance] = useState(account?.balance.toString() || '0');
  const [type, setType] = useState<AccountType>(account?.type || 'cash');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!account) {
      router.back();
    }
  }, [account]);

  const canSave = name.trim().length > 0;

  const handleUpdate = async () => {
    if (!canSave || !account) return;

    const parsedBalance = balance ? parseFloat(balance) : 0;
    if (Number.isNaN(parsedBalance)) {
      setError('Enter a valid balance');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await api.updateAccount(account.id, {
        name: name.trim(),
        type,
        balance: parsedBalance,
      });

      setAccounts(accounts.map((a) => (a.id === account.id ? response.data : a)));
      
      // Refresh summary
      const summaryResponse = await api.getDashboardSummary();
      setDashboardSummary(summaryResponse.data);
      
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch {
      setError('Failed to update account');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = () => {
    if (!account) return;

    Alert.alert(
      'Delete Account',
      'Are you sure you want to delete this account? All associated transactions will be affected.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsSubmitting(true);
              await api.deleteAccount(account.id);
              setAccounts(accounts.filter((a) => a.id !== account.id));
              
              const summaryResponse = await api.getDashboardSummary();
              setDashboardSummary(summaryResponse.data);
              
              router.back();
            } catch {
              Alert.alert('Error', 'Failed to delete account');
            } finally {
              setIsSubmitting(false);
            }
          },
        },
      ]
    );
  };

  if (!account) return null;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView
        style={styles.flex}
        contentContainerStyle={styles.content}
        showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag"
      >
        <View style={styles.header}>
          <Text style={styles.title}>Edit Account</Text>
          <Pressable onPress={() => router.back()} style={styles.closeButton}>
            <X size={20} color="#94A3B8" />
          </Pressable>
        </View>

        <View style={styles.section}>
          <NeonInput
            label="Account Name"
            placeholder="e.g. Main Bank"
            value={name}
            onChangeText={setName}
          />

          <View>
            <Text style={styles.sectionLabel}>Account Type</Text>
            <View style={styles.typeGrid}>
              {ACCOUNT_TYPES.map((item) => {
                const selected = type === item.key;
                return (
                  <Pressable
                    key={item.key}
                    onPress={() => {
                      setType(item.key);
                      Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                    }}
                    style={[styles.typeChip, selected ? styles.typeChipSelected : styles.typeChipIdle]}
                  >
                    {item.icon}
                    <Text style={[styles.typeChipText, selected ? styles.typeChipTextSelected : styles.typeChipTextIdle]}>
                      {item.label}
                    </Text>
                  </Pressable>
                );
              })}
            </View>
          </View>

          <NeonInput
            label="Current Balance"
            placeholder="0"
            keyboardType="decimal-pad"
            value={balance}
            onChangeText={setBalance}
            error={error || undefined}
          />
        </View>

        <View style={styles.footer}>
          <View style={styles.buttonWrap}>
            <NeonButton
              title="Save Changes"
              onPress={handleUpdate}
              isLoading={isSubmitting}
              disabled={!canSave || isSubmitting}
            />
          </View>
          
          <Pressable 
            onPress={handleDelete}
            className="mt-4 flex-row items-center justify-center p-4 rounded-2xl bg-red-500/10 border border-red-500/20"
          >
            <Trash2 size={20} color="#EF4444" />
            <Text className="ml-2 text-red-500 font-bold">Delete Account</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: {
    backgroundColor: '#020617',
    flex: 1,
  },
  flex: {
    flex: 1,
  },
  content: {
    paddingHorizontal: 24,
    paddingBottom: 40,
  },
  header: {
    alignItems: 'center',
    flexDirection: 'row',
    justifyContent: 'space-between',
    paddingVertical: 24,
  },
  title: {
    color: '#FFFFFF',
    fontSize: 20,
    fontWeight: '700',
  },
  closeButton: {
    alignItems: 'center',
    backgroundColor: '#0F172A',
    borderRadius: 999,
    height: 40,
    justifyContent: 'center',
    width: 40,
  },
  section: {
    gap: 24,
    marginBottom: 32,
  },
  sectionLabel: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '500',
    marginBottom: 12,
    marginLeft: 4,
  },
  typeGrid: {
    flexDirection: 'row',
    flexWrap: 'wrap',
    gap: 12,
  },
  typeChip: {
    alignItems: 'center',
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    paddingHorizontal: 16,
    paddingVertical: 12,
  },
  typeChipIdle: {
    backgroundColor: '#0F172A',
    borderColor: '#1E293B',
  },
  typeChipSelected: {
    backgroundColor: 'rgba(16, 185, 129, 0.2)',
    borderColor: '#10B981',
  },
  typeChipText: {
    fontSize: 16,
    fontWeight: '500',
    marginLeft: 8,
  },
  typeChipTextIdle: {
    color: '#94A3B8',
  },
  typeChipTextSelected: {
    color: '#FFFFFF',
  },
  footer: {
    marginTop: 'auto',
  },
  buttonWrap: {
    marginBottom: 8,
  },
});
