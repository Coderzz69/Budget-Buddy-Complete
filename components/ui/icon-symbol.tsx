import MaterialIcons from '@expo/vector-icons/MaterialIcons';
import FontAwesome6 from '@expo/vector-icons/FontAwesome6';
import React from 'react';
import { OpaqueColorValue, StyleProp, ViewStyle } from 'react-native';

const MAPPING: Record<string, { icon: string, lib: 'material' | 'fa' }> = {
  'dollarsign.circle.fill': { icon: 'circle-dollar-to-slot', lib: 'fa' },
  'cart.fill': { icon: 'cart-shopping', lib: 'fa' },
  'car.fill': { icon: 'car', lib: 'fa' },
  'gamecontroller.fill': { icon: 'gamepad', lib: 'fa' },
  'bolt.fill': { icon: 'bolt', lib: 'fa' },
  'heart.fill': { icon: 'heart', lib: 'fa' },
  'book.fill': { icon: 'book', lib: 'fa' },
  'chart.pie.fill': { icon: 'chart-pie', lib: 'fa' },
  'creditcard': { icon: 'credit-card', lib: 'fa' },
  'pencil': { icon: 'pen', lib: 'fa' },
  'trash': { icon: 'trash', lib: 'fa' },
  'magnifyingglass': { icon: 'magnifying-glass', lib: 'fa' },
  'person.circle': { icon: 'circle-user', lib: 'fa' },
  'plus': { icon: 'plus', lib: 'fa' },
  'arrow.down': { icon: 'arrow-down', lib: 'fa' },
  'arrow.up': { icon: 'arrow-up', lib: 'fa' },
  'list.bullet.rectangle.fill': { icon: 'list-check', lib: 'fa' },
  'bag.fill': { icon: 'bag-shopping', lib: 'fa' },
  'ellipsis.circle.fill': { icon: 'ellipsis', lib: 'fa' },
  'fork.knife': { icon: 'utensils', lib: 'fa' },
  'airplane': { icon: 'plane', lib: 'fa' },
  'doc.text.fill': { icon: 'file-lines', lib: 'fa' },
  'play.circle.fill': { icon: 'circle-play', lib: 'fa' },
  'shippingbox.fill': { icon: 'box', lib: 'fa' },
  'play.tv.fill': { icon: 'tv', lib: 'fa' },
  'cup.and.saucer.fill': { icon: 'mug-hot', lib: 'fa' },
  'applelogo': { icon: 'apple', lib: 'fa' },
  'creditcard.fill': { icon: 'credit-card', lib: 'fa' },
  'shield.fill': { icon: 'shield-halved', lib: 'fa' },
  'cart.badge.plus': { icon: 'cart-plus', lib: 'fa' },
  'graduationcap.fill': { icon: 'graduation-cap', lib: 'fa' },
  'leaf.fill': { icon: 'leaf', lib: 'fa' },
  'wineglass.fill': { icon: 'glass-martini-alt', lib: 'fa' },
  'fitness': { icon: 'dumbbell', lib: 'fa' },
};

export function IconSymbol({
  name,
  size = 24,
  color,
  style,
}: {
  name: string;
  size?: number;
  color: string | OpaqueColorValue;
  style?: StyleProp<ViewStyle>;
}) {
  const mapped = MAPPING[name];
  
  if (mapped?.lib === 'fa') {
    return <FontAwesome6 color={color} name={mapped.icon as any} size={size} style={style as any} />;
  }
  
  // Default to MaterialIcons if not found or mapped to material
  return <MaterialIcons color={color} name={(mapped?.icon || 'help-outline') as any} size={size} style={style as any} />;
}
