import React, { useCallback, useState, useRef, useEffect } from 'react';
import { View, Text, ScrollView, Pressable, ActivityIndicator, Modal, TextInput, Alert, Keyboard, TouchableWithoutFeedback, KeyboardAvoidingView, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context'
import { useFocusEffect } from 'expo-router';
import { useStore } from '../../store/useStore';
import { GlassCard } from '../../components/GlassCard';
import { NeonButton } from '../../components/NeonButton';
import { Plus, Target, AlertCircle, CheckCircle2, Layers, X, Trophy, Trash2 } from 'lucide-react-native';
import { formatCurrency } from '../../utils/formatters';
import { router } from 'expo-router';
import { EmptyState } from '../../components/EmptyState';
import { IconSymbol } from '../../components/ui/icon-symbol';
import { useApi, Goal } from '../../hooks/useApi';

type TabType = 'budgets' | 'goals';

function cn(...inputs: any[]) {
  return inputs.filter(Boolean).join(' ');
}

export default function Budget() {
  const { budgets, categories, isLoading } = useStore();
  const api = useApi();
  const apiRef = useRef(api);
  useEffect(() => { apiRef.current = api; }, [api]);

  const [activeTab, setActiveTab] = useState<TabType>('budgets');
  const [goals, setGoals] = useState<Goal[]>([]);
  const [goalsLoading, setGoalsLoading] = useState(false);
  const [showAddGoal, setShowAddGoal] = useState(false);

  // Form state
  const [goalName, setGoalName] = useState('');
  const [targetAmount, setTargetAmount] = useState('');
  const [savedAmount, setSavedAmount] = useState('');
  const [monthlyContribution, setMonthlyContribution] = useState('');
  const [submitting, setSubmitting] = useState(false);

  const totalLimit = budgets.reduce((sum, b) => sum + b.limit, 0);
  const totalSpent = budgets.reduce((sum, b) => sum + (b.spent || 0), 0);
  const overallProgress = totalLimit > 0 ? (totalSpent / totalLimit) : 0;

  const getCategoryName = (id: string) => categories.find(c => c.id === id)?.name || 'Category';

  const getProgressColor = (progress: number) => {
    if (progress >= 1) return '#EF4444';
    if (progress >= 0.8) return '#F59E0B';
    return '#10B981';
  };

  const loadGoals = useCallback(async () => {
    setGoalsLoading(true);
    try {
      const res = await apiRef.current.getGoals();
      setGoals(Array.isArray(res.data) ? res.data : []);
    } catch (e) {
      console.error('Failed to load goals:', e);
    } finally {
      setGoalsLoading(false);
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useFocusEffect(
    useCallback(() => {
      loadGoals();
    // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [])
  );

  const handleAddGoal = async () => {
    if (!goalName.trim() || !targetAmount || !monthlyContribution) {
      Alert.alert('Missing fields', 'Please fill in Goal Name, Target Amount, and Monthly Saving.');
      return;
    }
    const target = parseFloat(targetAmount);
    const saved = parseFloat(savedAmount || '0');
    const monthly = parseFloat(monthlyContribution);
    if (isNaN(target) || isNaN(monthly) || target <= 0 || monthly <= 0) {
      Alert.alert('Invalid values', 'Target and Monthly Saving must be positive numbers.');
      return;
    }
    setSubmitting(true);
    try {
      await apiRef.current.createGoal({
        name: goalName.trim(),
        target_amount: target,
        saved_amount: saved,
        monthly_contribution: monthly,
      });
      setGoalName('');
      setTargetAmount('');
      setSavedAmount('');
      setMonthlyContribution('');
      setShowAddGoal(false);
      await loadGoals();
    } catch (e) {
      Alert.alert('Error', 'Failed to create goal. Please try again.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteGoal = (id: string, name: string) => {
    Alert.alert('Delete Goal', `Remove "${name}"?`, [
      { text: 'Cancel', style: 'cancel' },
      {
        text: 'Delete',
        style: 'destructive',
        onPress: async () => {
          try {
            await apiRef.current.deleteGoal(id);
            setGoals(prev => prev.filter(g => g.id !== id));
          } catch {
            Alert.alert('Error', 'Failed to delete goal.');
          }
        },
      },
    ]);
  };

  if (isLoading) {
    return (
      <View className="flex-1 items-center justify-center bg-slate-950">
        <ActivityIndicator size="large" color="#10B981" />
      </View>
    );
  }

  return (
    <SafeAreaView className="flex-1 bg-slate-950" edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} keyboardShouldPersistTaps="handled" keyboardDismissMode="on-drag" className="flex-1">
        {/* Header */}
        <View className="px-6 py-4 flex-row items-center justify-between">
          <View>
            <Text className="text-white text-2xl font-bold">Budgets & Goals</Text>
            <Text className="text-slate-400 text-sm">Manage limits and track savings</Text>
          </View>
          <Pressable
            onPress={() => activeTab === 'budgets' ? router.push('/budgets/add') : setShowAddGoal(true)}
            className="bg-primary/10 p-2 rounded-xl border border-primary/20"
          >
            <Plus size={24} color="#10B981" />
          </Pressable>
        </View>

        {/* Tab Switcher */}
        <View className="flex-row mx-6 mb-5 bg-slate-900 rounded-2xl p-1">
          <Pressable
            className={cn(
              'flex-1 py-2.5 rounded-xl items-center',
              activeTab === 'budgets' ? 'bg-slate-700' : ''
            )}
            onPress={() => setActiveTab('budgets')}
          >
            <Text className={cn('font-semibold text-sm', activeTab === 'budgets' ? 'text-white' : 'text-slate-500')}>
              Budgets
            </Text>
          </Pressable>
          <Pressable
            className={cn(
              'flex-1 py-2.5 rounded-xl items-center',
              activeTab === 'goals' ? 'bg-slate-700' : ''
            )}
            onPress={() => setActiveTab('goals')}
          >
            <Text className={cn('font-semibold text-sm', activeTab === 'goals' ? 'text-white' : 'text-slate-500')}>
              Goals
            </Text>
          </Pressable>
        </View>

        {/* ── BUDGETS TAB ── */}
        {activeTab === 'budgets' && (
          <>
            {/* Global Progress Hero */}
            <View className="px-6 py-2">
              <GlassCard className="p-6 overflow-hidden" intensity="high">
                <View className="flex-row justify-between items-center mb-4">
                  <View>
                    <Text className="text-slate-400 text-sm font-medium">Total Monthly Limit</Text>
                    <Text className="text-white text-2xl font-bold">{formatCurrency(totalLimit)}</Text>
                  </View>
                  <View className="items-end">
                    <Text className="text-slate-400 text-sm font-medium">Spent so far</Text>
                    <Text className="text-white text-lg font-semibold">{formatCurrency(totalSpent)}</Text>
                  </View>
                </View>
                <View className="h-3 w-full bg-slate-900 rounded-full overflow-hidden mb-4">
                  <View
                    className="h-full rounded-full"
                    style={{
                      width: `${Math.min(overallProgress * 100, 100)}%`,
                      backgroundColor: getProgressColor(overallProgress)
                    }}
                  />
                </View>
                <View className="flex-row items-center">
                  {overallProgress >= 1 ? (
                    <AlertCircle size={16} color="#EF4444" />
                  ) : (
                    <CheckCircle2 size={16} color="#10B981" />
                  )}
                  <Text className={cn(
                    'text-xs font-medium ml-2',
                    overallProgress >= 1 ? 'text-red-400' : 'text-emerald-400'
                  )}>
                    {overallProgress >= 1
                      ? 'You have exceeded your overall budget'
                      : `${formatCurrency(totalLimit - totalSpent)} remaining for this month`}
                  </Text>
                </View>
              </GlassCard>
            </View>

            {/* Individual Budgets */}
            <View className="px-6 py-4 mb-10">
              <View className="flex-row items-center justify-between mb-4">
                <Text className="text-white text-lg font-bold">Category Limits</Text>
                <NeonButton title="Adjust" variant="ghost" size="sm" textClassName="text-primary" />
              </View>
              <View className="gap-4">
                {budgets.length === 0 ? (
                  <EmptyState
                    icon={Layers}
                    title="No budgets yet"
                    description="Set monthly limits for your categories to track spending."
                    actionLabel="Create Budget"
                    onAction={() => router.push('/budgets/add')}
                  />
                ) : (
                  budgets.map((budget) => {
                    const spent = budget.spent || 0;
                    const progress = spent / budget.limit;
                    return (
                      <Pressable key={budget.id} onPress={() => router.push(`/budgets/${budget.id}`)}>
                        <GlassCard className="p-5">
                          <View className="flex-row justify-between items-center mb-3">
                            <View className="flex-row items-center">
                              <View className="w-10 h-10 rounded-xl bg-slate-900 items-center justify-center mr-3">
                                <IconSymbol
                                  name={categories.find(c => c.id === budget.categoryId)?.icon || 'ellipsis.circle.fill'}
                                  size={20}
                                  color={getProgressColor(progress)}
                                />
                              </View>
                              <View>
                                <Text className="text-white font-bold">{getCategoryName(budget.categoryId)}</Text>
                                <Text className="text-slate-400 text-xs">{formatCurrency(budget.limit)} limit</Text>
                              </View>
                            </View>
                            <View className="items-end">
                              <Text className="text-white font-bold">{formatCurrency(spent)}</Text>
                              <Text className="text-slate-400 text-xs">spent</Text>
                            </View>
                          </View>
                          <View className="h-2 w-full bg-slate-900 rounded-full overflow-hidden">
                            <View
                              className="h-full rounded-full"
                              style={{
                                width: `${Math.min(progress * 100, 100)}%`,
                                backgroundColor: getProgressColor(progress)
                              }}
                            />
                          </View>
                        </GlassCard>
                      </Pressable>
                    );
                  })
                )}
              </View>
            </View>
          </>
        )}

        {/* ── GOALS TAB ── */}
        {activeTab === 'goals' && (
          <View className="px-6 pb-24">
            {goalsLoading ? (
              <View className="items-center py-12">
                <ActivityIndicator size="large" color="#38BDF8" />
              </View>
            ) : goals.length === 0 ? (
              <EmptyState
                icon={Target}
                title="No goals yet"
                description="Add a savings goal like 'Buy a bike' and track your progress."
                actionLabel="Add Goal"
                onAction={() => setShowAddGoal(true)}
              />
            ) : (
              <View className="gap-4">
                {goals.map((goal) => {
                  const progressWidth = `${goal.progress_pct}%`;
                  const isComplete = goal.progress_pct >= 100;
                  return (
                    <GlassCard key={goal.id} className="p-5 border-slate-800/50" intensity="high">
                      <View className="flex-row items-start justify-between mb-4">
                        <View className="flex-row items-center flex-1">
                          <View className="w-11 h-11 rounded-2xl bg-blue-500/20 items-center justify-center mr-3">
                            {isComplete
                              ? <Trophy size={20} color="#F59E0B" />
                              : <Target size={20} color={goal.color || '#38BDF8'} />
                            }
                          </View>
                          <View className="flex-1">
                            <Text className="text-white font-bold text-base">{goal.name}</Text>
                            <Text className="text-slate-400 text-xs">
                              {isComplete ? '🎉 Goal reached!' : `${goal.months_remaining ?? '—'} months to go`}
                            </Text>
                          </View>
                        </View>
                        <Pressable onPress={() => handleDeleteGoal(goal.id, goal.name)} className="p-1">
                          <Trash2 size={16} color="#EF4444" />
                        </Pressable>
                      </View>

                      {/* Amount Row */}
                      <View className="flex-row justify-between mb-3">
                        <View>
                          <Text className="text-slate-400 text-[10px] uppercase tracking-widest">Saved</Text>
                          <Text className="text-white font-bold">{formatCurrency(goal.saved_amount)}</Text>
                        </View>
                        <View className="items-center">
                          <Text className="text-slate-400 text-[10px] uppercase tracking-widest">Monthly</Text>
                          <Text className="text-blue-400 font-bold">{formatCurrency(goal.monthly_contribution)}</Text>
                        </View>
                        <View className="items-end">
                          <Text className="text-slate-400 text-[10px] uppercase tracking-widest">Target</Text>
                          <Text className="text-white font-bold">{formatCurrency(goal.target_amount)}</Text>
                        </View>
                      </View>

                      {/* Progress Bar */}
                      <View className="mb-3">
                        <View className="flex-row justify-between mb-1">
                          <Text className="text-slate-400 text-xs">{goal.progress_pct.toFixed(1)}% complete</Text>
                          <Text className="text-slate-400 text-xs">
                            {formatCurrency(goal.target_amount - goal.saved_amount)} left
                          </Text>
                        </View>
                        <View className="h-2 w-full bg-slate-800 rounded-full overflow-hidden">
                          <View
                            className="h-full rounded-full"
                            style={{
                              width: progressWidth,
                              backgroundColor: isComplete ? '#F59E0B' : (goal.color || '#38BDF8')
                            }}
                          />
                        </View>
                      </View>

                      {/* Tip Banner */}
                      {!isComplete && goal.months_remaining != null && (
                        <View className="bg-slate-900/60 p-3 rounded-xl border border-slate-800/40">
                          <Text className="text-slate-300 text-xs">
                            <Text className="text-emerald-400 font-bold">Good! </Text>
                            At ₹{goal.monthly_contribution.toLocaleString()}/month you can reach this goal in{' '}
                            <Text className="text-white font-bold">{goal.months_remaining} month{goal.months_remaining !== 1 ? 's' : ''}</Text>.
                          </Text>
                        </View>
                      )}
                    </GlassCard>
                  );
                })}
              </View>
            )}
          </View>
        )}
      </ScrollView>

      {/* Add Goal Modal */}
      <Modal visible={showAddGoal} transparent animationType="slide" onRequestClose={() => setShowAddGoal(false)}>
        <TouchableWithoutFeedback onPress={Keyboard.dismiss} accessible={false}>
          <View className="flex-1 bg-black/60 justify-end">
            <KeyboardAvoidingView
              behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            >
              <TouchableWithoutFeedback accessible={false}>
                <View className="bg-slate-900 rounded-t-3xl px-6 pt-6 pb-10 border-t border-slate-800">
                  <View className="flex-row items-center justify-between mb-6">
                    <Text className="text-white text-xl font-bold">New Savings Goal</Text>
                    <Pressable onPress={() => { Keyboard.dismiss(); setShowAddGoal(false); }}>
                      <X size={22} color="#94A3B8" />
                    </Pressable>
                  </View>

                  {/* Goal Name */}
                  <Text className="text-slate-400 text-xs mb-1 uppercase tracking-widest">Goal Name</Text>
                  <TextInput
                    value={goalName}
                    onChangeText={setGoalName}
                    placeholder="e.g. Honda Shine, MacBook Pro"
                    placeholderTextColor="#475569"
                    returnKeyType="next"
                    blurOnSubmit={false}
                    className="bg-slate-800 text-white px-4 py-3 rounded-xl mb-4"
                  />

                  {/* Target Amount */}
                  <Text className="text-slate-400 text-xs mb-1 uppercase tracking-widest">Target Amount (₹)</Text>
                  <TextInput
                    value={targetAmount}
                    onChangeText={setTargetAmount}
                    placeholder="e.g. 80000"
                    placeholderTextColor="#475569"
                    keyboardType="numeric"
                    returnKeyType="next"
                    blurOnSubmit={false}
                    className="bg-slate-800 text-white px-4 py-3 rounded-xl mb-4"
                  />

                  {/* Already Saved */}
                  <Text className="text-slate-400 text-xs mb-1 uppercase tracking-widest">Already Saved (₹)</Text>
                  <TextInput
                    value={savedAmount}
                    onChangeText={setSavedAmount}
                    placeholder="e.g. 0"
                    placeholderTextColor="#475569"
                    keyboardType="numeric"
                    returnKeyType="next"
                    blurOnSubmit={false}
                    className="bg-slate-800 text-white px-4 py-3 rounded-xl mb-4"
                  />

                  {/* Monthly Saving */}
                  <Text className="text-slate-400 text-xs mb-1 uppercase tracking-widest">Monthly Saving (₹)</Text>
                  <TextInput
                    value={monthlyContribution}
                    onChangeText={setMonthlyContribution}
                    placeholder="e.g. 5000"
                    placeholderTextColor="#475569"
                    keyboardType="numeric"
                    returnKeyType="done"
                    onSubmitEditing={Keyboard.dismiss}
                    className="bg-slate-800 text-white px-4 py-3 rounded-xl mb-6"
                  />

                  <Pressable
                    onPress={() => { Keyboard.dismiss(); handleAddGoal(); }}
                    disabled={submitting}
                    className="bg-blue-600 py-4 rounded-xl items-center"
                  >
                    {submitting
                      ? <ActivityIndicator color="#fff" />
                      : <Text className="text-white font-bold text-base">Add Goal</Text>
                    }
                  </Pressable>
                </View>
              </TouchableWithoutFeedback>
            </KeyboardAvoidingView>
          </View>
        </TouchableWithoutFeedback>
      </Modal>
    </SafeAreaView>
  );
}
