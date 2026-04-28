import React from 'react';
import { View, Text, ScrollView, Pressable, Alert } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router } from 'expo-router';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../../components/GlassCard';
import { EmptyState } from '../../components/EmptyState';
import { ArrowLeft, Filter, Trash2, Edit2, CreditCard } from 'lucide-react-native';
import { formatCurrency } from '../../utils/formatters';
import { IconSymbol } from '../../components/ui/icon-symbol';
import { getTransactionIcon } from '../../utils/icons';
import { Swipeable, RectButton } from 'react-native-gesture-handler';
import { useApi } from '../../hooks/useApi';
import * as Haptics from 'expo-haptics';

export default function Transactions() {
  const { transactions, setTransactions, isLoading, setDashboardSummary, setAccounts, categories } = useStore();
  const api = useApi();

  const handleDelete = (id: string) => {
    Alert.alert(
      'Delete Transaction',
      'Are you sure you want to delete this transaction?',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              await api.deleteTransaction(id);
              setTransactions(transactions.filter(t => t.id !== id));
              // Refresh summary and accounts
              const [summaryRes, accountsRes] = await Promise.all([
                api.getDashboardSummary(),
                api.getAccounts()
              ]);
              setDashboardSummary(summaryRes.data);
              setAccounts(accountsRes.data);
            } catch (error) {
              Alert.alert('Error', 'Failed to delete transaction');
            }
          }
        }
      ]
    );
  };

  const renderRightActions = (id: string) => {
    return (
      <RectButton
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Medium);
          handleDelete(id);
        }}
      >
        <View className="bg-rose-500 justify-center items-end px-10 h-20 rounded-2xl mb-3">
          <Trash2 size={24} color="#FFF" />
        </View>
      </RectButton>
    );
  };

  const renderLeftActions = (id: string) => {
    return (
      <RectButton
        onPress={() => {
          Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
          router.push(`/transactions/${id}`);
        }}
      >
        <View className="bg-emerald-500 justify-center items-start px-10 h-20 rounded-2xl mb-3">
          <Edit2 size={24} color="#FFF" />
        </View>
      </RectButton>
    );
  };

  return (
    <SafeAreaView className="flex-1 bg-slate-950" edges={['top']}>
      <View className="px-6 py-4 flex-row items-center justify-between border-b border-slate-900">
        <View className="flex-row items-center">
          <Pressable onPress={() => router.back()} className="mr-4">
            <ArrowLeft size={24} color="#FFF" />
          </Pressable>
          <Text className="text-white text-2xl font-bold">Activities</Text>
        </View>
        <Pressable className="bg-slate-900 p-2 rounded-xl border border-slate-800">
          <Filter size={20} color="#94A3B8" />
        </Pressable>
      </View>

      <ScrollView showsVerticalScrollIndicator={false} className="flex-1 px-6 py-4">
        {transactions.length === 0 ? (
          <EmptyState
            icon={CreditCard}
            title="No transactions yet"
            description="Start by adding an expense or income."
            actionLabel="Add Transaction"
            onAction={() => router.push('/transactions/add')}
          />
        ) : (
          <View className="gap-3 mb-24">
            {transactions.map((transaction) => {
              const category = categories.find(c => c.id === transaction.categoryId);
              return (
                <Swipeable
                  key={transaction.id}
                  renderRightActions={() => renderRightActions(transaction.id)}
                  renderLeftActions={() => renderLeftActions(transaction.id)}
                  friction={2}
                  rightThreshold={40}
                  leftThreshold={40}
                >
                  <GlassCard className="p-4 border-slate-800/50 bg-slate-900/40">
                    <View className="flex-row items-center justify-between">
                      <View className="flex-row items-center flex-1">
                        <View 
                          className="w-12 h-12 rounded-xl items-center justify-center mr-4"
                          style={{ backgroundColor: category?.color ? `${category.color}20` : '#0F172A', borderColor: category?.color || '#1E293B', borderWidth: 1 }}
                        >
                          <IconSymbol 
                            name={getTransactionIcon(category?.name, transaction.note)} 
                            size={24} 
                            color={category?.color || '#94A3B8'} 
                          />
                        </View>
                        <View className="flex-1 mr-4">
                          <Text className="text-white font-bold text-base" numberOfLines={1}>
                            {transaction.note || 'No description'}
                          </Text>
                          <Text className="text-slate-400 text-xs uppercase">
                            {category?.name || 'Uncategorized'} • {new Date(transaction.occurredAt).toLocaleDateString()}
                          </Text>
                        </View>
                      </View>
                      <Text className={`font-bold text-base ${transaction.type === 'income' ? 'text-emerald-400' : 'text-white'}`}>
                        {transaction.type === 'income' ? '+' : '-'}{formatCurrency(transaction.amount)}
                      </Text>
                    </View>
                  </GlassCard>
                </Swipeable>
              );
            })}
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
