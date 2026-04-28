import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { Ionicons } from '@expo/vector-icons';
import { BlurView } from 'expo-blur';

interface AlertData {
    id: string;
    alert_type: string;
    message: string;
    created_at: string;
}

interface AlertProps {
    alerts: AlertData[];
    onDismiss: (id: string) => void;
}

export const WeekendOverspendAlert: React.FC<AlertProps> = ({ alerts, onDismiss }) => {
    if (alerts.length === 0) return null;

    return (
        <View className="mt-6 px-2">
            {alerts.map(alert => (
                <View key={alert.id} className="mb-3 rounded-3xl overflow-hidden border border-red-500/20">
                    <BlurView intensity={20} tint="dark" className="p-4 flex-row items-center">
                        <View className="bg-red-500/20 p-2 rounded-xl mr-4">
                            <Ionicons 
                                name={alert.alert_type === 'weekend_warning' ? "cafe-outline" : "alert-circle-outline"} 
                                size={22} 
                                color="#EF4444" 
                            />
                        </View>
                        <View className="flex-1">
                            <Text className="text-white font-semibold text-sm leading-tight">
                                {alert.message}
                            </Text>
                        </View>
                        <TouchableOpacity onPress={() => onDismiss(alert.id)} className="p-2">
                            <Ionicons name="close" size={20} color="#94A3B8" />
                        </TouchableOpacity>
                    </BlurView>
                </View>
            ))}
        </View>
    );
};
