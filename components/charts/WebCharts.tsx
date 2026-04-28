import React from 'react';
import { View, Text } from 'react-native';
import Svg, { Circle, Line as SvgLine, Path, Text as SvgText } from 'react-native-svg';
import { formatCurrency } from '../../utils/formatters';

type LinePoint = {
  x: string | number;
  y: number;
  label?: string;
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

  const points = data.map((point, index) => ({
    x: padding + (index * chartWidth) / Math.max(data.length - 1, 1),
    y: padding + chartHeight - (point.y / maxValue) * chartHeight
  }));

  // Create smooth path
  let pathD = `M ${points[0].x},${points[0].y}`;
  for (let i = 0; i < points.length - 1; i++) {
    const p0 = points[i];
    const p1 = points[i + 1];
    const cpX = (p0.x + p1.x) / 2;
    pathD += ` C ${cpX},${p0.y} ${cpX},${p1.y} ${p1.x},${p1.y}`;
  }

  return (
    <View className="w-full items-center">
      <Svg width="100%" viewBox={`0 0 ${width} ${height}`}>
        {[0, 0.5, 1].map((ratio) => {
          const y = padding + chartHeight * (1 - ratio);
          return (
            <React.Fragment key={ratio}>
              <SvgLine
                x1={padding}
                y1={y}
                x2={width - padding}
                y2={y}
                stroke="rgba(255,255,255,0.08)"
                strokeWidth="1"
              />
              <SvgText
                x={padding - 4}
                y={y + 3}
                fill="#64748B"
                fontSize="8"
                textAnchor="end"
              >
                {ratio === 0 ? '0' : formatCurrency(maxValue * ratio).split('.')[0]}
              </SvgText>
            </React.Fragment>
          );
        })}

        <Path
          d={pathD}
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
                {point.label || point.x}
              </SvgText>
            </React.Fragment>
          );
        })}
      </Svg>
    </View>
  );
}

export function WebCategoryChart({ data, total }: WebCategoryChartProps) {
  const size = 200;
  const radius = size / 2;
  const innerRadius = 60;
  const center = size / 2;

  let currentAngle = 0;

  return (
    <View className="w-full items-center">
      <View className="h-[250px] w-full items-center justify-center">
        <Svg width={size} height={size} viewBox={`0 0 ${size} ${size}`}>
          {data.map((item, index) => {
            const angle = (item.value / total) * 360;
            if (angle <= 0) return null;
            
            // Handle full circle case
            if (angle >= 359.9) {
              return (
                <Circle 
                  key={item.label}
                  cx={center} 
                  cy={center} 
                  r={(radius + innerRadius) / 2} 
                  stroke={item.color}
                  strokeWidth={radius - innerRadius}
                  fill="none"
                />
              );
            }

            const startAngle = currentAngle;
            const endAngle = currentAngle + angle;
            currentAngle += angle;

            // Arcs are better drawn in radians
            const toRad = (deg: number) => (deg * Math.PI) / 180;
            
            const x1 = center + radius * Math.cos(toRad(startAngle));
            const y1 = center + radius * Math.sin(toRad(startAngle));
            const x2 = center + radius * Math.cos(toRad(endAngle));
            const y2 = center + radius * Math.sin(toRad(endAngle));

            const ix1 = center + innerRadius * Math.cos(toRad(startAngle));
            const iy1 = center + innerRadius * Math.sin(toRad(startAngle));
            const ix2 = center + innerRadius * Math.cos(toRad(endAngle));
            const iy2 = center + innerRadius * Math.sin(toRad(endAngle));

            const largeArcFlag = angle > 180 ? 1 : 0;

            const d = `
              M ${x1} ${y1}
              A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}
              L ${ix2} ${iy2}
              A ${innerRadius} ${innerRadius} 0 ${largeArcFlag} 0 ${ix1} ${iy1}
              Z
            `;

            return <Path key={item.label} d={d} fill={item.color} />;
          })}
        </Svg>
        <View className="absolute items-center justify-center">
          <Text className="text-slate-400 text-[10px] font-medium uppercase tracking-widest">Spent</Text>
          <Text className="text-white text-xl font-bold">{formatCurrency(total).split('.')[0]}</Text>
        </View>
      </View>
    </View>
  );
}
