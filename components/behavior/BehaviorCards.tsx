import React from 'react';
import { View, Text } from 'react-native';
import { Ionicons } from '@expo/vector-icons';

interface BehaviorProfile {
    salary_credit_date_expected: number | null;
    weekend_overspend_ratio: number;
    average_monthly_burn: number;
}

export const BehaviorCards: React.FC<{ profile: BehaviorProfile }> = ({ profile }) => {
    return (
        <View className="flex-row flex-wrap justify-between mt-4">
            {/* Salary Card */}
            <View className="w-[48%] bg-surface p-5 rounded-[28px] mb-4 border border-white/5">
                <View className="bg-emerald-500/10 self-start p-2 rounded-xl mb-3">
                    <Ionicons name="wallet-outline" size={20} color="#10B981" />
                </View>
                <Text className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">Expected Payday</Text>
                <Text className="text-white text-xl font-bold">
                    {profile.salary_credit_date_expected ? `Day ${profile.salary_credit_date_expected}` : '---'}
                </Text>
            </View>

            {/* Burn Rate Card */}
            <View className="w-[48%] bg-surface p-5 rounded-[28px] mb-4 border border-white/5">
                <View className="bg-amber-500/10 self-start p-2 rounded-xl mb-3">
                    <Ionicons name="flame-outline" size={20} color="#F59E0B" />
                </View>
                <Text className="text-gray-400 text-xs font-medium uppercase tracking-wider mb-1">Monthly Burn</Text>
                <Text className="text-white text-xl font-bold">
                    ${profile.average_monthly_burn?.toLocaleString() || '0'}
                </Text>
            </View>

            {/* Weekend Ratio Card */}
            <View className="w-full bg-surface p-5 rounded-[28px] border border-white/5 flex-row items-center justify-between">
                <View className="flex-row items-center">
                    <View className="bg-sky-500/10 p-3 rounded-2xl mr-4">
                        <Ionicons name="calendar-outline" size={24} color="#38BDF8" />
                    </View>
                    <View>
                        <Text className="text-gray-400 text-xs font-medium uppercase tracking-wider">Weekend Surge</Text>
                        <Text className="text-white text-lg font-bold">
                            {profile.weekend_overspend_ratio > 1 
                                ? `${Math.round((profile.weekend_overspend_ratio - 1) * 100)}% higher spend`
                                : 'Steady spending'}
                        </Text>
                    </View>
                </View>
                {profile.weekend_overspend_ratio > 1.2 && (
                    <Ionicons name="warning-outline" size={24} color="#EF4444" />
                )}
            </View>
        </View>
    );
};
