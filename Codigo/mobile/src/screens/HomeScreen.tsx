import React from 'react';
import { View, Text, TouchableOpacity } from 'react-native';
import { useAuth } from '@/context/AuthContext';

export default function HomeScreen() {
  const { signOut } = useAuth();

  return (
    <View className="flex-1 bg-gray-50 items-center justify-center">
      <Text className="text-3xl font-bold text-gray-800 mb-2">Cognita</Text>
      <Text className="text-base text-gray-500 mb-12">Área principal do aplicativo.</Text>

      <TouchableOpacity
        className="bg-primary rounded-xl px-8 py-3 items-center"
        onPress={signOut}
        activeOpacity={0.8}
      >
        <Text className="text-white font-semibold text-base">Sair</Text>
      </TouchableOpacity>
    </View>
  );
}
