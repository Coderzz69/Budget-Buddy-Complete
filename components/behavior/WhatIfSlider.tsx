import React, { useState } from 'react';
import { View, Text } from 'react-native';
import Slider from '@react-native-community/slider';
import { Ionicons } from '@expo/vector-icons';

interface WhatIfSliderProps {
    onValueChange: (value: number) => void;
    currentMonthlyBurn: number;
}

export const WhatIfSlider: React.FC<WhatIfSliderProps> = ({ onValueChange, currentMonthlyBurn }) => {
    const [reduction, setReduction] = useState(0);

    const handleSlidingComplete = (value: number) => {
        setReduction(value);
        onValueChange(value);
    };

    return (
        <View className="mt-8 p-6 bg-surface rounded-[40px] border border-emerald-500/10 shadow-2xl shadow-emerald-500/5">
            <View className="flex-row items-center mb-6">
                <View className="bg-emerald-500/10 p-3 rounded-2xl mr-4">
                    <Ionicons name="sparkles-outline" size={24} color="#10B981" />
                </View>
                <View>
                    <Text className="text-white text-lg font-bold">"What-If" Simulator</Text>
                    <Text className="text-gray-400 text-xs">Simulate savings and see the impact</Text>
                </View>
            </View>

            <View className="mb-8">
                <View className="flex-row justify-between items-end mb-4">
                    <Text className="text-gray-400 text-sm font-medium">Daily cutback amount</Text>
                    <View className="flex-row items-baseline">
                        <Text className="text-emerald-400 text-3xl font-black">${reduction}</Text>
                        <Text className="text-gray-500 text-xs ml-1">/day</Text>
                    </View>
                </View>

                <Slider
                    style={{ width: '100%', height: 40 }}
                    minimumValue={0}
                    maximumValue={100}
                    step={5}
                    value={reduction}
                    onSlidingComplete={handleSlidingComplete}
                    minimumTrackTintColor="#10B981"
                    maximumTrackTintColor="#334155"
                    thumbTintColor="#10B981"
                />
            </View>

            <View className="bg-white/5 p-4 rounded-2xl">
                <Text className="text-gray-300 text-sm text-center">
                    Reducing daily spend by <Text className="text-emerald-400 font-bold">${reduction}</Text> could extend your balance by approximately 
                    <Text className="text-white font-bold"> {Math.round((reduction * 30 / (currentMonthlyBurn / 30 || 1)))} extra days </Text>
                    each month.
                </Text>
            </View>
        </View>
    );
};
