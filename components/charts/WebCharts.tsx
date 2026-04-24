import React from 'react';
import { View, Text } from 'react-native';
import Svg, { Circle, Line as SvgLine, Polyline, Text as SvgText } from 'react-native-svg';
import { formatCurrency } from '../../utils/formatters';

type LinePoint = {
  x: string;
  y: number;
};

type CategoryPoint = {
  label: string;
  value: number;
  color: string;
};

interface WebLineChartProps {
  data: LinePoint[];
}

interface WebCategoryChartProps {
  data: CategoryPoint[];
  total: number;
}

export function WebLineChart({ data }: WebLineChartProps) {
  const width = 320;
  const height = 180;
  const padding = 24;
  const chartWidth = width - padding * 2;
  const chartHeight = height - padding * 2;
  const maxValue = Math.max(...data.map((point) => point.y), 1);

  const points = data
    .map((point, index) => {
      const x = padding + (index * chartWidth) / Math.max(data.length - 1, 1);
      const y = padding + chartHeight - (point.y / maxValue) * chartHeight;
      return `${x},${y}`;
    })
    .join(' ');

  return (
    <View className="w-full items-center">
      <Svg width="100%" viewBox={`0 0 ${width} ${height}`}>
        {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
          const y = padding + chartHeight * ratio;
          return (
            <SvgLine
              key={ratio}
              x1={padding}
              y1={y}
              x2={width - padding}
              y2={y}
              stroke="rgba(255,255,255,0.08)"
              strokeWidth="1"
            />
          );
        })}

        <Polyline
          points={points}
          fill="none"
          stroke="#10B981"
          strokeWidth="3"
          strokeLinejoin="round"
          strokeLinecap="round"
        />

        {data.map((point, index) => {
          const x = padding + (index * chartWidth) / Math.max(data.length - 1, 1);
          const y = padding + chartHeight - (point.y / maxValue) * chartHeight;
          return (
            <React.Fragment key={point.x}>
              <Circle cx={x} cy={y} r="4" fill="#10B981" />
              <SvgText
                x={x}
                y={height - 4}
                fill="#64748B"
                fontSize="10"
                textAnchor="middle"
              >
                {point.x}
              </SvgText>
            </React.Fragment>
          );
        })}
      </Svg>
    </View>
  );
}

export function WebCategoryChart({ data, total }: WebCategoryChartProps) {
  const maxValue = Math.max(...data.map((item) => item.value), 1);

  return (
    <View className="w-full gap-4">
      <View className="items-center justify-center rounded-[28px] border border-slate-800 bg-slate-950/70 px-6 py-8">
        <Text className="text-slate-400 text-xs font-medium uppercase tracking-widest">Spent</Text>
        <Text className="mt-2 text-white text-2xl font-bold">{formatCurrency(total)}</Text>
      </View>

      <View className="gap-3">
        {data.map((item) => {
          const percentage = total > 0 ? (item.value / total) * 100 : 0;
          const barWidth = Math.max((item.value / maxValue) * 224, 18);

          return (
            <View key={item.label} className="gap-2">
              <View className="flex-row items-center justify-between">
                <View className="flex-row items-center">
                  <View
                    className="mr-3 h-3 w-3 rounded-full"
                    style={{ backgroundColor: item.color }}
                  />
                  <Text className="text-white font-medium">{item.label}</Text>
                </View>
                <Text className="text-slate-400 text-sm">{percentage.toFixed(0)}%</Text>
              </View>
              <View className="h-3 overflow-hidden rounded-full bg-slate-900">
                <View className="h-3 rounded-full" style={{ width: barWidth, backgroundColor: item.color }} />
              </View>
            </View>
          );
        })}
      </View>
    </View>
  );
}
