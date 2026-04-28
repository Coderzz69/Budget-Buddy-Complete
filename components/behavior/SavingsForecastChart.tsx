import React from 'react';
import { View, Dimensions, Text } from 'react-native';
import { LineChart } from 'react-native-chart-kit';
import { useColorScheme } from 'react-native';

interface ForecastData {
    date: string;
    predicted_balance: number;
}

interface SavingsForecastChartProps {
    data: ForecastData[];
}

export const SavingsForecastChart: React.FC<SavingsForecastChartProps> = ({ data }) => {
    const screenWidth = Dimensions.get('window').width;
    const colorScheme = useColorScheme();

    if (!data || data.length === 0) {
        return (
            <View className="h-40 items-center justify-center bg-surface rounded-3xl">
                <Text className="text-gray-400">No trajectory data available</Text>
            </View>
        );
    }

    // Downsample data if too many points for the chart
    const labels = data.filter((_, i) => i % 7 === 0).map(d => d.date.split('-')[2]); // Just day
    const dataset = data.map(d => d.predicted_balance);

    const chartConfig = {
        backgroundGradientFrom: "#1E293B",
        backgroundGradientTo: "#0F172A",
        decimalPlaces: 0,
        color: (opacity = 1) => `rgba(16, 185, 129, ${opacity})`, // Emerald Green
        labelColor: (opacity = 1) => `rgba(148, 163, 184, ${opacity})`,
        style: {
            borderRadius: 16
        },
        propsForDots: {
            r: "4",
            strokeWidth: "2",
            stroke: "#10B981"
        }
    };

    return (
        <View className="mt-4 p-4 bg-surface rounded-[32px] overflow-hidden border border-white/5">
            <Text className="text-white font-bold text-lg mb-4 ml-2">30-Day Cash Trajectory</Text>
            <LineChart
                data={{
                    labels: labels,
                    datasets: [{
                        data: dataset
                    }]
                }}
                width={screenWidth - 64}
                height={220}
                chartConfig={chartConfig}
                bezier
                style={{
                    marginVertical: 8,
                    borderRadius: 16
                }}
            />
            <View className="flex-row justify-between px-4 mt-2">
                <Text className="text-gray-500 text-xs text-center">Current</Text>
                <Text className="text-gray-500 text-xs text-center">+30 Days</Text>
            </View>
        </View>
    );
};
