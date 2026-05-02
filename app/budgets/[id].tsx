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
import { X, Trash2, Target } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';

import { NeonButton } from '../../components/NeonButton';
import { NeonInput } from '../../components/NeonInput';
import { useApi } from '../../hooks/useApi';
import { useStore } from '../../store/useStore';

export default function EditBudget() {
  const { id } = useLocalSearchParams();
  const api = useApi();
  const { budgets, setBudgets, categories } = useStore();

  const budget = budgets.find((b) => b.id === id);
  const category = categories.find((c) => c.id === budget?.categoryId);

  const [limit, setLimit] = useState(budget?.limit.toString() || '');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!budget) {
      router.back();
    }
  }, [budget]);

  const handleUpdate = async () => {
    const parsedLimit = parseFloat(limit);
    if (Number.isNaN(parsedLimit) || parsedLimit <= 0) {
      setError('Please enter a valid limit');
      return;
    }

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await api.updateBudget(budget!.id, {
        limit: parsedLimit,
      });

      setBudgets(budgets.map((b) => (b.id === budget!.id ? response.data : b)));
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch {
      setError('Failed to update budget');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = () => {
    Alert.alert(
      'Delete Budget',
      'Are you sure you want to remove this budget limit?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsSubmitting(true);
              await api.deleteBudget(budget!.id);
              setBudgets(budgets.filter((b) => b.id !== budget!.id));
              router.back();
            } catch {
              Alert.alert('Error', 'Failed to delete budget');
            } finally {
              setIsSubmitting(false);
            }
          },
        },
      ]
    );
  };

  if (!budget) return null;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView style={styles.flex} contentContainerStyle={styles.content} keyboardShouldPersistTaps="handled">
        <View style={styles.header}>
          <Text style={styles.title}>Edit Budget</Text>
          <Pressable onPress={() => router.back()} style={styles.closeButton}>
            <X size={20} color="#94A3B8" />
          </Pressable>
        </View>

        <View style={styles.section}>
          <View className="items-center justify-center p-8 rounded-3xl bg-slate-900 border border-slate-800 mb-4">
            <View 
              className="w-16 h-16 rounded-2xl items-center justify-center mb-4"
              style={{ backgroundColor: category?.color || '#10B981' }}
            >
              <Text className="text-3xl">{category?.icon || '📅'}</Text>
            </View>
            <Text className="text-white text-xl font-bold">{category?.name || 'Category'}</Text>
            <Text className="text-slate-400">Monthly Budget</Text>
          </View>

          <NeonInput
            label="Monthly Limit"
            placeholder="0"
            keyboardType="decimal-pad"
            value={limit}
            onChangeText={setLimit}
            error={error || undefined}
          />
        </View>

        <View style={styles.footer}>
          <NeonButton
            title="Update Budget"
            onPress={handleUpdate}
            isLoading={isSubmitting}
            disabled={!limit || isSubmitting}
          />
          
          <Pressable 
            onPress={handleDelete}
            className="mt-4 flex-row items-center justify-center p-4 rounded-2xl bg-red-500/10 border border-red-500/20"
          >
            <Trash2 size={20} color="#EF4444" />
            <Text className="ml-2 text-red-500 font-bold">Remove Budget</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#020617' },
  flex: { flex: 1 },
  content: { padding: 24 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 24 },
  title: { color: '#FFF', fontSize: 20, fontWeight: '700' },
  closeButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#0F172A', alignItems: 'center', justifyContent: 'center' },
  section: { gap: 16, marginBottom: 32 },
  footer: { marginTop: 'auto' },
});
