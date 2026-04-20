import React from 'react';
import {
  StyleProp,
  StyleSheet,
  Text,
  TextInput,
  TextInputProps,
  TextStyle,
  View,
  ViewStyle,
} from 'react-native';

interface NeonInputProps extends TextInputProps {
  label?: string;
  error?: string;
  containerClassName?: string;
  className?: string;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
  containerStyle?: StyleProp<ViewStyle>;
  inputWrapperStyle?: StyleProp<ViewStyle>;
  inputStyle?: StyleProp<TextStyle>;
}

export function NeonInput({
  label,
  error,
  leftIcon,
  rightIcon,
  containerStyle,
  inputWrapperStyle,
  inputStyle,
  ...props
}: NeonInputProps) {
  return (
    <View style={[styles.container, containerStyle]}>
      {label ? <Text style={styles.label}>{label}</Text> : null}

      <View
        style={[
          styles.inputWrapper,
          styles.inputWrapperIdle,
          error ? styles.inputWrapperError : null,
          inputWrapperStyle,
        ]}
      >
        {leftIcon ? <View style={styles.leftIcon}>{leftIcon}</View> : null}

        <TextInput
          style={[styles.input, inputStyle]}
          placeholderTextColor="#64748B"
          autoCapitalize="none"
          autoCorrect={false}
          blurOnSubmit={false}
          {...props}
        />

        {rightIcon ? <View style={styles.rightIcon}>{rightIcon}</View> : null}
      </View>

      {error ? <Text style={styles.error}>{error}</Text> : null}
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    gap: 6,
    width: '100%',
  },
  label: {
    color: '#94A3B8',
    fontSize: 14,
    fontWeight: '500',
    marginLeft: 4,
  },
  inputWrapper: {
    alignItems: 'center',
    backgroundColor: 'rgba(15, 23, 42, 0.5)',
    borderRadius: 16,
    borderWidth: 1,
    flexDirection: 'row',
    minHeight: 56,
    paddingHorizontal: 16,
  },
  inputWrapperIdle: {
    borderColor: '#1E293B',
  },
  inputWrapperError: {
    borderColor: '#EF4444',
  },
  leftIcon: {
    marginRight: 12,
  },
  rightIcon: {
    marginLeft: 12,
  },
  input: {
    color: '#FFFFFF',
    flex: 1,
    fontSize: 16,
    paddingVertical: 12,
  },
  error: {
    color: '#EF4444',
    fontSize: 12,
    fontWeight: '500',
    marginLeft: 4,
    marginTop: 2,
  },
});
