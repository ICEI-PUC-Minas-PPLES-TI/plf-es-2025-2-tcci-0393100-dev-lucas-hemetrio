import React, { useState } from 'react';
import {
  View,
  Text,
  TextInput,
  TouchableOpacity,
  KeyboardAvoidingView,
  Platform,
  ActivityIndicator,
  Alert,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AuthStackParamList } from '@/navigation/RootNavigator';
import { authService } from '@/services/authService';
import { useAuth } from '@/context/AuthContext';

type Props = NativeStackScreenProps<AuthStackParamList, 'Login'>;

export default function LoginScreen({ navigation }: Props) {
  const { signIn } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleLogin = async () => {
    if (!email.trim() || !password) return;

    setLoading(true);
    try {
      await authService.login({ email: email.trim(), password });
      signIn();
    } catch {
      Alert.alert('Erro', 'Email ou senha incorretos.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <KeyboardAvoidingView
      className="flex-1 bg-gray-50"
      behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
    >
      <View className="flex-1 flex-row">
        {/* Painel esquerdo — branding */}
        <View className="flex-1 bg-primary items-center justify-center px-12">
          <Text className="text-5xl font-bold text-white mb-4">Cognita</Text>
          <Text className="text-lg text-blue-100 text-center leading-relaxed">
            Gerencie seus documentos{'\n'}e conexões de conhecimento.
          </Text>
        </View>

        {/* Painel direito — formulário */}
        <View className="flex-1 items-center justify-center px-12">
          <View className="w-full max-w-sm">
            <Text className="text-2xl font-bold text-gray-800 mb-1">Bem-vindo de volta</Text>
            <Text className="text-sm text-gray-500 mb-8">Acesse sua conta para continuar.</Text>

            <View className="mb-4">
              <Text className="text-sm font-medium text-gray-600 mb-1">Email</Text>
              <TextInput
                className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-800"
                placeholder="seu@email.com"
                placeholderTextColor="#9CA3AF"
                value={email}
                onChangeText={setEmail}
                keyboardType="email-address"
                autoCapitalize="none"
                autoCorrect={false}
              />
            </View>

            <View className="mb-6">
              <Text className="text-sm font-medium text-gray-600 mb-1">Senha</Text>
              <TextInput
                className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-800"
                placeholder="••••••••"
                placeholderTextColor="#9CA3AF"
                value={password}
                onChangeText={setPassword}
                secureTextEntry
              />
            </View>

            <TouchableOpacity
              className="bg-primary rounded-xl py-3.5 items-center"
              onPress={handleLogin}
              disabled={loading}
              activeOpacity={0.8}
            >
              {loading ? (
                <ActivityIndicator color="#fff" />
              ) : (
                <Text className="text-white font-semibold text-base">Entrar</Text>
              )}
            </TouchableOpacity>

            <TouchableOpacity
              className="mt-5 items-center"
              onPress={() => navigation.navigate('Register')}
            >
              <Text className="text-gray-500 text-sm">
                Não tem uma conta?{' '}
                <Text className="text-primary font-semibold">Cadastre-se</Text>
              </Text>
            </TouchableOpacity>
          </View>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
