import React, { useState, useEffect } from 'react';
import {
  Pressable,
  ScrollView,
  StyleSheet,
  Text,
  View,
  Alert,
} from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { router, useLocalSearchParams } from 'expo-router';
import { X, Trash2 } from 'lucide-react-native';
import * as Haptics from 'expo-haptics';

import { NeonButton } from '../../components/NeonButton';
import { NeonInput } from '../../components/NeonInput';
import { useApi } from '../../hooks/useApi';
import { useStore } from '../../store/useStore';

const COLORS = ['#10B981', '#3B82F6', '#8B5CF6', '#EC4899', '#F59E0B', '#EF4444', '#64748B'];
const ICONS = ['🏷️', '🍔', '🚗', '🛍️', '🏠', '🎬', '💊', '🎓', '💡', '💰'];

export default function EditCategory() {
  const { id } = useLocalSearchParams();
  const api = useApi();
  const { categories, setCategories } = useStore();

  const category = categories.find((c) => c.id === id);

  const [name, setName] = useState(category?.name || '');
  const [icon, setIcon] = useState(category?.icon || '🏷️');
  const [color, setColor] = useState(category?.color || '#10B981');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    if (!category) {
      router.back();
    }
  }, [category]);

  const canSave = name.trim().length > 0;

  const handleUpdate = async () => {
    if (!canSave || !category) return;

    try {
      setIsSubmitting(true);
      setError(null);

      const response = await api.updateCategory(category.id, {
        name: name.trim(),
        icon,
        color,
      });

      setCategories(categories.map((c) => (c.id === category.id ? response.data : c)));
      Haptics.notificationAsync(Haptics.NotificationFeedbackType.Success);
      router.back();
    } catch {
      setError('Failed to update category');
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleDelete = () => {
    if (!category) return;

    Alert.alert(
      'Delete Category',
      'Are you sure you want to delete this category? Associated transactions will lose their category label.',
      [
        { text: 'Cancel', style: 'cancel' },
        {
          text: 'Delete',
          style: 'destructive',
          onPress: async () => {
            try {
              setIsSubmitting(true);
              await api.deleteCategory(category.id);
              setCategories(categories.filter((c) => c.id !== category.id));
              router.back();
            } catch {
              Alert.alert('Error', 'Failed to delete category');
            } finally {
              setIsSubmitting(false);
            }
          },
        },
      ]
    );
  };

  if (!category) return null;

  return (
    <SafeAreaView style={styles.safeArea} edges={['top']}>
      <ScrollView style={styles.flex} contentContainerStyle={styles.content}>
        <View style={styles.header}>
          <Text style={styles.title}>Edit Category</Text>
          <Pressable onPress={() => router.back()} style={styles.closeButton}>
            <X size={20} color="#94A3B8" />
          </Pressable>
        </View>

        <View style={styles.section}>
          <NeonInput
            label="Category Name"
            placeholder="e.g. Groceries"
            value={name}
            onChangeText={setName}
          />

          <View>
            <Text style={styles.label}>Icon</Text>
            <View style={styles.grid}>
              {ICONS.map((i) => (
                <Pressable
                  key={i}
                  onPress={() => {
                    setIcon(i);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                  style={[styles.item, icon === i && styles.itemSelected]}
                >
                  <Text style={styles.itemText}>{i}</Text>
                </Pressable>
              ))}
            </View>
          </View>

          <View>
            <Text style={styles.label}>Color</Text>
            <View style={styles.grid}>
              {COLORS.map((c) => (
                <Pressable
                  key={c}
                  onPress={() => {
                    setColor(c);
                    Haptics.impactAsync(Haptics.ImpactFeedbackStyle.Light);
                  }}
                  style={[styles.item, { backgroundColor: c }, color === c && styles.colorItemSelected]}
                />
              ))}
            </View>
          </View>
        </View>

        <View style={styles.footer}>
          <NeonButton
            title="Save Changes"
            onPress={handleUpdate}
            isLoading={isSubmitting}
            disabled={!canSave || isSubmitting}
          />
          
          <Pressable 
            onPress={handleDelete}
            className="mt-4 flex-row items-center justify-center p-4 rounded-2xl bg-red-500/10 border border-red-500/20"
          >
            <Trash2 size={20} color="#EF4444" />
            <Text className="ml-2 text-red-500 font-bold">Delete Category</Text>
          </Pressable>
        </View>
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safeArea: { flex: 1, backgroundColor: '#020617' },
  flex: { flex: 1 },
  content: { padding: 24 },
  header: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 },
  title: { color: '#FFF', fontSize: 20, fontWeight: '700' },
  closeButton: { width: 40, height: 40, borderRadius: 20, backgroundColor: '#0F172A', alignItems: 'center', justifyContent: 'center' },
  section: { gap: 24, marginBottom: 32 },
  label: { color: '#94A3B8', fontSize: 14, marginBottom: 12 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', gap: 12 },
  item: { width: 48, height: 48, borderRadius: 12, backgroundColor: '#0F172A', alignItems: 'center', justifyContent: 'center', borderWidth: 1, borderColor: 'transparent' },
  itemSelected: { borderColor: '#10B981', backgroundColor: 'rgba(16, 185, 129, 0.1)' },
  itemText: { fontSize: 20 },
  colorItemSelected: { borderWidth: 2, borderColor: '#FFF' },
  footer: { marginTop: 'auto' },
});
