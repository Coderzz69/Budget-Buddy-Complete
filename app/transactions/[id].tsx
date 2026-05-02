import React, { useState, useEffect } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  Alert,
  TextInput,
  KeyboardAvoidingView,
  Platform,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { X, Trash2, Calendar, Check, Info } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';

import { GlassCard } from '../../components/GlassCard';
import { NeonButton } from '../../components/NeonButton';
import { IconSymbol } from '../../components/ui/icon-symbol';
import { useApi } from '../../hooks/useApi';
import { useStore, TransactionType } from '../../store/useStore';

export default function EditTransaction() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const api = useApi();
  const { transactions, setTransactions, accounts, categories, setAccounts, setDashboardSummary } = useStore();

  const transaction = transactions.find((t) => t.id === id);

  const [type, setType] = useState<TransactionType>(transaction?.type || 'expense');
  const [amount, setAmount] = useState(transaction?.amount.toString() || '');
  const [selectedCategory, setSelectedCategory] = useState(transaction?.categoryId || '');
  const [selectedAccount, setSelectedAccount] = useState(transaction?.accountId || '');
  const [note, setNote] = useState(transaction?.note || '');
  const [date, setDate] = useState(transaction?.occurredAt.split('T')[0] || new Date().toISOString().split('T')[0]);
  const [isSubmitting, setIsSubmitting] = useState(false);

  useEffect(() => {
    if (!transaction) {
      router.back();
    }
  }, [transaction]);

  if (!transaction) return null;

  const canSave = amount && !isNaN(parseFloat(amount)) && selectedCategory && selectedAccount;

  const handleUpdate = async () => {
    const parsedAmount = parseFloat(amount);
    if (!canSave || isSubmitting) return;

    try {
      setIsSubmitting(true);
      const response = await api.updateTransaction(transaction.id, {
        amount: parsedAmount,
        type,
        accountId: selectedAccount,
        categoryId: selectedCategory,
        occurredAt: date + 'T00:00:00Z',
        note: note || undefined,
      });

      setTransactions(transactions.map((t) => (t.id === transaction.id ? response.data : t)));
      
      const [accountsResponse, summaryResponse] = await Promise.all([
        api.getAccounts(),
        api.getDashboardSummary(),
      ]);
      setAccounts(accountsResponse.data);
      setDashboardSummary(summaryResponse.data);

      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch (error) {
      Alert.alert('Error', 'Failed to update transaction');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = () => {
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
              setIsSubmitting(true);
              await api.deleteTransaction(transaction.id);
              setTransactions(transactions.filter((t) => t.id !== transaction.id));
              
              const [accountsResponse, summaryResponse] = await Promise.all([
                api.getAccounts(),
                api.getDashboardSummary(),
              ]);
              setAccounts(accountsResponse.data);
              setDashboardSummary(summaryResponse.data);
              
              router.back();
            } catch (error) {
              Alert.alert('Error', 'Failed to delete transaction');
            } finally {
              setIsSubmitting(false);
            }
          },
        },
      ]
    );
  };

  return (
    <KeyboardAvoidingView 
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
      className="flex-1 bg-slate-950"
    >
      <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" className="flex-1 px-6">
        {/* Header */}
        <View className="flex-row items-center justify-between py-6">
          <Text className="text-white text-xl font-bold">Edit Transaction</Text>
          <Pressable 
            onPress={() => router.back()}
            className="w-10 h-10 rounded-full bg-slate-900 items-center justify-center"
          >
            <X size={20} color="#94A3B8" />
          </Pressable>
        </View>

        {/* Type Toggle */}
        <View className="flex-row bg-slate-900 p-1.5 rounded-2xl mb-8">
          <Pressable 
            onPress={() => { setType('expense'); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
            className={`flex-1 py-3 rounded-xl items-center ${type === 'expense' ? 'bg-slate-800' : ''}`}
          >
            <Text className={`font-bold ${type === 'expense' ? 'text-white' : 'text-slate-500'}`}>Expense</Text>
          </Pressable>
          <Pressable 
            onPress={() => { setType('income'); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
            className={`flex-1 py-3 rounded-xl items-center ${type === 'income' ? 'bg-slate-800' : ''}`}
          >
            <Text className={`font-bold ${type === 'income' ? 'text-white' : 'text-slate-500'}`}>Income</Text>
          </Pressable>
        </View>

        {/* Amount Input */}
        <View className="items-center mb-10">
          <Text className="text-slate-500 text-sm font-medium mb-2 uppercase tracking-widest">Amount</Text>
          <TextInput
            value={amount}
            onChangeText={setAmount}
            placeholder="0.00"
            placeholderTextColor="#1E293B"
            keyboardType="decimal-pad"
            className={`text-6xl font-bold text-center h-20 min-w-[200px] ${type === 'income' ? 'text-emerald-400' : 'text-white'}`}
          />
        </View>

        {/* Form Fields */}
        <View className="gap-6 mb-10">
          {/* Category Selector */}
          <View>
            <Text className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-3 ml-1">Category</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="-mx-6 px-6">
              <View className="flex-row gap-3 pr-12">
                {categories.map((cat) => (
                  <Pressable
                    key={cat.id}
                    onPress={() => { setSelectedCategory(cat.id); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
                    className={`px-4 py-3 rounded-2xl border items-center justify-center flex-row min-w-[100px] ${
                      selectedCategory === cat.id 
                        ? 'bg-emerald-500/20 border-emerald-500' 
                        : 'bg-slate-900 border-slate-900'
                    }`}
                  >
                    <View className="mr-2">
                       <IconSymbol 
                        name={cat.icon || 'ellipsis.circle.fill'} 
                        size={18} 
                        color={selectedCategory === cat.id ? '#FFF' : '#64748B'} 
                      />
                    </View>
                    <Text className={`font-medium text-sm ${selectedCategory === cat.id ? 'text-white' : 'text-slate-400'}`}>
                      {cat.name}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </ScrollView>
          </View>

          {/* Account Selector */}
          <View>
            <Text className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-3 ml-1">Source Account</Text>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} className="-mx-6 px-6">
              <View className="flex-row gap-3 pr-12">
                {accounts.map((account) => (
                  <Pressable
                    key={account.id}
                    onPress={() => { setSelectedAccount(account.id); Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light); }}
                    className={`px-4 py-3 rounded-2xl border items-center justify-center flex-row min-w-[120px] ${
                      selectedAccount === account.id 
                        ? 'bg-emerald-500/20 border-emerald-500' 
                        : 'bg-slate-900 border-slate-900'
                    }`}
                  >
                    <Check size={16} color={selectedAccount === account.id ? '#10B981' : '#64748B'} />
                    <Text className={`font-medium text-sm ml-2 ${selectedAccount === account.id ? 'text-white' : 'text-slate-400'}`}>
                      {account.name}
                    </Text>
                  </Pressable>
                ))}
              </View>
            </ScrollView>
          </View>

          {/* Date & Note */}
          <View className="flex-row gap-4">
            <View className="flex-1">
               <Text className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-3 ml-1">Date</Text>
               <GlassCard className="px-4 h-14 justify-center border-slate-900">
                  <View className="flex-row items-center">
                    <Calendar size={16} color="#475569" className="mr-2" />
                    <Text className="text-white font-medium">{date}</Text>
                  </View>
               </GlassCard>
            </View>
            <View className="flex-[1.5]">
               <Text className="text-slate-500 text-xs font-bold uppercase tracking-widest mb-3 ml-1">Note</Text>
               <GlassCard className="px-4 h-14 justify-center border-slate-900">
                  <TextInput
                    value={note}
                    onChangeText={setNote}
                    placeholder="Lunch with friends..."
                    placeholderTextColor="#475569"
                    className="text-white font-medium"
                  />
               </GlassCard>
            </View>
          </View>
        </View>

        {/* Action Buttons */}
        <View className="gap-4 mb-20">
          <NeonButton 
            title="Update Transaction" 
            onPress={handleUpdate}
            className="h-16"
            isLoading={isSubmitting}
            disabled={!canSave || isSubmitting}
          />
          
          <Pressable 
            onPress={handleDelete}
            className="h-16 rounded-2xl items-center justify-center bg-rose-500/10 border border-rose-500/20"
          >
            <View className="flex-row items-center">
              <Trash2 size={20} color="#F43F5E" />
              <Text className="text-rose-500 font-bold ml-2">Delete Transaction</Text>
            </View>
          </Pressable>
        </View>
      </ScrollView>
    </KeyboardAvoidingView>
  );
}
