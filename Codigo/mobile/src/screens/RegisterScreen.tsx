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
  ScrollView,
} from 'react-native';
import { NativeStackScreenProps } from '@react-navigation/native-stack';
import { AuthStackParamList } from '@/navigation/RootNavigator';
import { authService } from '@/services/authService';
import { useAuth } from '@/context/AuthContext';

type Props = NativeStackScreenProps<AuthStackParamList, 'Register'>;

export default function RegisterScreen({ navigation }: Props) {
  const { signIn } = useAuth();
  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!name.trim() || !email.trim() || !password) return;

    if (password !== confirmPassword) {
      Alert.alert('Erro', 'As senhas não coincidem.');
      return;
    }

    setLoading(true);
    try {
      await authService.register({ name: name.trim(), email: email.trim(), password });
      await authService.login({ email: email.trim(), password });
      Alert.alert('Conta criada!', 'Bem-vindo ao Cognita.', [
        { text: 'Continuar', onPress: signIn },
      ]);
    } catch (error: any) {
      const detail = error?.response?.data?.detail;
      Alert.alert(
        'Erro',
        detail === 'Email already registered'
          ? 'Email já cadastrado.'
          : 'Não foi possível criar a conta.',
      );
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
            Organize seu conhecimento{'\n'}de forma inteligente.
          </Text>
        </View>

        {/* Painel direito — formulário */}
        <View className="flex-1 justify-center px-12">
          <ScrollView
            showsVerticalScrollIndicator={false}
            keyboardShouldPersistTaps="handled"
            contentContainerStyle={{ paddingVertical: 32 }}
          >
            <View className="w-full max-w-sm self-center">
              <Text className="text-2xl font-bold text-gray-800 mb-1">Criar conta</Text>
              <Text className="text-sm text-gray-500 mb-8">Comece a organizar seu conhecimento.</Text>

              <View className="mb-4">
                <Text className="text-sm font-medium text-gray-600 mb-1">Nome</Text>
                <TextInput
                  className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-800"
                  placeholder="Seu nome"
                  placeholderTextColor="#9CA3AF"
                  value={name}
                  onChangeText={setName}
                  autoCapitalize="words"
                />
              </View>

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

              <View className="mb-4">
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

              <View className="mb-8">
                <Text className="text-sm font-medium text-gray-600 mb-1">Confirmar senha</Text>
                <TextInput
                  className="bg-white border border-gray-200 rounded-xl px-4 py-3 text-base text-gray-800"
                  placeholder="••••••••"
                  placeholderTextColor="#9CA3AF"
                  value={confirmPassword}
                  onChangeText={setConfirmPassword}
                  secureTextEntry
                />
              </View>

              <TouchableOpacity
                className="bg-primary rounded-xl py-3.5 items-center"
                onPress={handleRegister}
                disabled={loading}
                activeOpacity={0.8}
              >
                {loading ? (
                  <ActivityIndicator color="#fff" />
                ) : (
                  <Text className="text-white font-semibold text-base">Criar conta</Text>
                )}
              </TouchableOpacity>

              <TouchableOpacity
                className="mt-5 items-center"
                onPress={() => navigation.goBack()}
              >
                <Text className="text-gray-500 text-sm">
                  Já tem uma conta?{' '}
                  <Text className="text-primary font-semibold">Entrar</Text>
                </Text>
              </TouchableOpacity>
            </View>
          </ScrollView>
        </View>
      </View>
    </KeyboardAvoidingView>
  );
}
