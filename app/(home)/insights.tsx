import React, { useCallback, useState } from 'react';
import { View, Text, ScrollView, Pressable, Platform } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { useFocusEffect } from 'expo-router';
import { GlassCard } from '../../components/GlassCard';
import { PolarChart, Pie } from 'victory-native';
import { ChevronLeft, ChevronRight, TrendingUp, Sparkles, Search, Scissors, TrendingDown } from 'lucide-react-native';
import { formatCurrency } from '../../utils/formatters';
import { SkeletonLoader } from '../../components/SkeletonLoader';
import { EmptyState } from '../../components/EmptyState';
import { cn } from '../../utils/cn';
import { WebCategoryChart } from '../../components/charts/WebCharts';
import { InsightsMonthlyResponse, InsightCard, useApi } from '../../hooks/useApi';
import { IconSymbol } from '../../components/ui/icon-symbol';

const PALETTE = ['#10B981', '#38BDF8', '#F59E0B', '#EF4444', '#A855F7', '#F97316', '#14B8A6', '#EAB308'];

export default function Insights() {
  const api = useApi();
  const [currentDate, setCurrentDate] = useState(new Date());
  const [insights, setInsights] = useState<InsightsMonthlyResponse | null>(null);
  const [isInsightsLoading, setIsInsightsLoading] = useState(false);
  const [error, setError] = useState('');

  const monthString = `${currentDate.getFullYear()}-${String(currentDate.getMonth() + 1).padStart(2, '0')}`;

  const loadInsights = useCallback(async () => {
    setIsInsightsLoading(true);
    setError('');
    try {
      const response = await api.getMonthlyInsights(monthString);
      setInsights(response.data);
    } catch (err) {
      console.error('Failed to load insights:', err);
      setError('Unable to load insights for this month.');
    } finally {
      setIsInsightsLoading(false);
    }
  }, [api, monthString]);

  useFocusEffect(
    useCallback(() => {
      loadInsights();
    }, [loadInsights])
  );

  const today = new Date();
  const maxDate = new Date(today.getFullYear(), today.getMonth(), 1);
  const minDate = new Date(2025, 9, 1); // Oct 2025

  const shiftMonth = (delta: number) => {
    setCurrentDate(prev => {
      const next = new Date(prev.getFullYear(), prev.getMonth() + delta, 1);
      if (next > maxDate) return prev;
      if (next < minDate) return prev;
      return next;
    });
  };

  const canGoPrev = currentDate > minDate;
  const canGoNext = currentDate < maxDate;

  const chartData = (insights?.top_categories || []).map((item, index) => ({
    label: item.category,
    value: Number(item.amount),
    color: (item as any).color || PALETTE[index % PALETTE.length],
  }));

  const totalSpending = insights?.total_spent || 0;
  const loading = isInsightsLoading;

  return (
    <SafeAreaView className="flex-1 bg-slate-950" edges={['top']}>
      <ScrollView showsVerticalScrollIndicator={false} className="flex-1">
        {/* Header */}
        <View className="px-6 py-4">
          <Text className="text-white text-2xl font-bold">Insights</Text>
          <Text className="text-slate-400 text-sm">Analyze your spending patterns</Text>
        </View>

        {/* Month Selector */}
        <View className="flex-row items-center justify-between px-6 mb-6">
          <Pressable 
            onPress={() => canGoPrev && shiftMonth(-1)} 
            disabled={!canGoPrev}
            className={cn(
              "p-2 rounded-full border border-slate-800",
              canGoPrev ? "bg-slate-900" : "bg-slate-900/40 opacity-40"
            )}
          >
            <ChevronLeft size={20} color={canGoPrev ? "#94A3B8" : "#475569"} />
          </Pressable>
          <Text className="text-white text-lg font-semibold">
            {currentDate.toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}
          </Text>
          <Pressable 
            onPress={() => canGoNext && shiftMonth(1)} 
            disabled={!canGoNext}
            className={cn(
              "p-2 rounded-full border border-slate-800",
              canGoNext ? "bg-slate-900" : "bg-slate-900/40 opacity-40"
            )}
          >
            <ChevronRight size={20} color={canGoNext ? "#94A3B8" : "#475569"} />
          </Pressable>
        </View>

        {error ? (
          <View className="px-6 mb-6">
            <GlassCard className="p-5 border-rose-500/30 bg-rose-500/10" intensity="medium">
               <Text className="text-rose-400">{error}</Text>
            </GlassCard>
          </View>
        ) : null}

        {/* Total Spend Summary Map */}
        <View className="px-6 mb-6">
          <GlassCard className="p-5 border-slate-800/50" intensity="high">
            <View className="flex-row items-center justify-between">
              <View className="flex-1">
                <Text className="text-slate-400 text-xs font-medium uppercase tracking-widest mb-2">Total Spend</Text>
                {(loading && !insights) ? (
                  <SkeletonLoader width={140} height={28} />
                ) : (
                  <Text className="text-white text-3xl font-bold">{formatCurrency(totalSpending)}</Text>
                )}
              </View>
            </View>
            <View className="flex-row items-center justify-between mt-4">
               {(loading && !insights) ? (
                 <SkeletonLoader width={120} height={24} borderRadius={12} />
               ) : (
                 <View className={cn(
                   'px-3 py-1.5 rounded-full',
                   !insights
                     ? 'bg-slate-800'
                     : (insights.percent_change <= 0 ? 'bg-emerald-500/15' : 'bg-rose-500/15')
                 )}>
                   <Text className={cn(
                     'text-xs font-semibold',
                     !insights
                       ? 'text-slate-300'
                       : (insights.percent_change <= 0 ? 'text-emerald-400' : 'text-rose-400')
                   )}>
                     {!insights 
                       ? 'Loading...' 
                       : `${insights.percent_change <= 0 ? 'Down' : 'Up'} ${Math.abs(insights.percent_change).toFixed(1)}% vs previous`}
                   </Text>
                 </View>
               )}
            </View>
          </GlassCard>
        </View>

        {/* Chart Section */}
        <View className="items-center justify-center mb-8">
          <GlassCard className="w-[90%] p-6 items-center justify-center" intensity="medium">
            <View className="h-64 w-64 items-center justify-center">
              {(loading && !insights) ? (
                <SkeletonLoader width={250} height={250} borderRadius={125} />
              ) : chartData.length > 0 ? (
                Platform.OS === 'web' ? (
                  <View className="w-full">
                    <WebCategoryChart data={chartData} total={totalSpending} />
                  </View>
                ) : (
                  <View className="h-64 w-64 items-center justify-center">
                    <PolarChart
                      data={chartData}
                      labelKey="label"
                      valueKey="value"
                      colorKey="color"
                      containerStyle={{ width: 250, height: 250 }}
                    >
                      <Pie.Chart innerRadius={80} />
                    </PolarChart>
                    <View className="absolute items-center justify-center pointer-events-none">
                      <Text className="text-slate-400 text-[10px] font-medium uppercase tracking-widest">Spent</Text>
                      <Text className="text-white text-xl font-bold">{formatCurrency(totalSpending).split('.')[0]}</Text>
                    </View>
                  </View>
                )
              ) : (
                <View className="h-64 w-64 items-center justify-center">
                  <EmptyState 
                    icon={Search} 
                    title="No Data" 
                    description="No spending data in this period." 
                  />
                </View>
              )}
            </View>
          </GlassCard>
        </View>

        {/* New Insight Cards (Includes Spotlight & Positive Trends) */}
        <View className="px-6 mb-8 gap-4">
          {(loading && !insights) ? (
             <GlassCard className="p-5 border-slate-800/50" intensity="high">
                <View className="flex-row items-center">
                    <SkeletonLoader width={48} height={48} borderRadius={16} className="mr-4" />
                    <View className="flex-1">
                       <SkeletonLoader width={100} height={16} className="mb-2" />
                       <SkeletonLoader width={180} height={20} />
                    </View>
                </View>
             </GlassCard>
           ) : (insights?.insight_cards && insights.insight_cards.length > 0) ? (
              insights.insight_cards.map((card: InsightCard, idx: number) => {
                const isSpotlight = card.kind === 'spotlight';
                const isSuccess = card.tone === 'success';
                const isWarning = card.tone === 'warning' || card.kind === 'spike';
                
                return (
                  <GlassCard 
                    key={card.id || `card-${idx}`} 
                    className={cn(
                      "p-5 border-slate-800/50",
                      isSpotlight ? "bg-primary/10 border-primary/30" : ""
                    )} 
                    intensity={isSpotlight ? "high" : "medium"}
                  >
                    <View className="flex-row items-center">
                      <View className={cn(
                        "w-12 h-12 rounded-2xl items-center justify-center mr-4",
                        isSuccess || card.kind === 'opportunity' ? "bg-emerald-500/15" : 
                        (card.kind === 'reduction' ? "bg-amber-500/15" : 
                        (isWarning ? "bg-rose-500/15" : "bg-blue-500/15"))
                      )}>
                        {isSpotlight || card.kind === 'opportunity' ? (
                           <Sparkles size={22} color={isSpotlight ? "#38BDF8" : "#10B981"} />
                        ) : card.kind === 'reduction' ? (
                           <Scissors size={22} color="#F59E0B" />
                        ) : isSuccess ? (
                           <TrendingUp size={22} color="#10B981" />
                        ) : (
                           <TrendingUp size={22} color="#F43F5E" />
                        )}
                      </View>
                      <View className="flex-1">
                        <Text className={cn(
                          "text-xs font-medium uppercase tracking-widest",
                          isSuccess || card.kind === 'opportunity' ? "text-emerald-400" : 
                          (card.kind === 'reduction' ? "text-amber-400" : 
                          (isWarning ? "text-rose-400" : "text-blue-400"))
                        )}>{card.title}</Text>
                        <Text className="text-white text-base font-bold mt-1">{card.message}</Text>
                        {card.footer ? <Text className="text-slate-500 text-xs mt-2">{card.footer}</Text> : null}
                      </View>
                    </View>
                  </GlassCard>
                );
              })
           ) : (!loading || insights) && chartData.length > 0 ? (
             <GlassCard className="p-5 flex-row items-center border-slate-800/50" intensity="high">
                <View className="w-12 h-12 rounded-2xl items-center justify-center mr-4 bg-emerald-500/15">
                  <Sparkles size={22} color="#10B981" />
                </View>
                <View className="flex-1">
                  <Text className="text-emerald-400 text-xs font-medium uppercase tracking-widest">Looking Good</Text>
                  <Text className="text-white text-base font-bold mt-1">Daily Flow Consistent</Text>
                  <Text className="text-slate-500 text-xs mt-2">No unusual spending patterns detected.</Text>
                </View>
             </GlassCard>
           ) : null}
        </View>

        {/* Category Breakdown */}
        {((!loading || insights) && chartData.length > 0) && (
          <View className="px-6 mb-24">
            <Text className="text-white text-lg font-bold mb-4">Breakdown</Text>
            <View className="gap-3">
              {(insights?.top_categories || []).map((cat, index) => (
                <GlassCard key={cat.category} className="flex-row items-center p-4">
                  <View 
                    className="w-10 h-10 rounded-xl mr-4 items-center justify-center opacity-80"
                    style={{ backgroundColor: (cat as any).color ? `${(cat as any).color}20` : `${PALETTE[index % PALETTE.length]}20` }}
                  >
                    <IconSymbol 
                      name={(cat as any).icon || 'ellipsis.circle.fill'} 
                      size={20} 
                      color={(cat as any).color || PALETTE[index % PALETTE.length]} 
                    />
                  </View>
                  <View className="flex-1 mr-4">
                    <View className="flex-row justify-between items-center mb-1">
                      <Text className="text-white font-medium">{cat.category}</Text>
                      {(cat as any).budget > 0 && (
                        <Text className="text-slate-400 text-[10px]">
                          of {formatCurrency((cat as any).budget)}
                        </Text>
                      )}
                    </View>
                    {(cat as any).budget > 0 ? (
                      <View className="h-1.5 w-full bg-white/10 rounded-full overflow-hidden">
                        <View 
                          className="h-full rounded-full"
                          style={{ 
                            width: `${Math.min((cat.amount / (cat as any).budget) * 100, 100)}%`,
                            backgroundColor: cat.amount > (cat as any).budget ? '#EF4444' : ((cat as any).color || PALETTE[index % PALETTE.length])
                          }}
                        />
                      </View>
                    ) : (
                      <Text className="text-slate-500 text-[10px]">No budget set</Text>
                    )}
                  </View>
                  <View className="items-end">
                    <Text className="text-white font-bold">{formatCurrency(cat.amount)}</Text>
                    <Text className="text-slate-400 text-[10px]">{cat.percentage.toFixed(0)}% of spend</Text>
                  </View>
                </GlassCard>
              ))}
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}
