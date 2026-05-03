import { Keyboard, TouchableWithoutFeedback, View, Platform } from 'react-native';
import React from 'react';

/**
 * Wraps children and dismisses the keyboard when the user taps
 * anywhere outside a focused TextInput.
 *
 * On iOS, the `onStartShouldSetResponder` trick is needed because
 * ScrollView consumes touches before they can bubble up to a
 * TouchableWithoutFeedback parent.
 */
export function DismissKeyboard({ children }: { children: React.ReactNode }) {
  return (
    <View
      style={{ flex: 1 }}
      onStartShouldSetResponder={() => {
        Keyboard.dismiss();
        return false; // Don't consume the event — let it pass through
      }}
    >
      {children}
    </View>
  );
}
