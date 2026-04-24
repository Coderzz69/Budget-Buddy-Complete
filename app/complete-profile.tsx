import { useSignUp, useAuth, useUser } from '@clerk/expo';
import * as DocumentPicker from 'expo-document-picker';
import { api, syncUser } from '@/utils/api';
import { LinearGradient } from 'expo-linear-gradient';
import { useRouter } from 'expo-router';
import React, { useEffect, useState } from 'react';
import {
    ActivityIndicator,
    KeyboardAvoidingView,
    Platform,
    ScrollView,
    StyleSheet,
    Text,
    TextInput,
    TouchableOpacity,
    View
} from 'react-native';
import Animated, { FadeInDown } from 'react-native-reanimated';
import CustomAlert from '@/components/CustomAlert';

export default function CompleteProfileScreen() {
    const router = useRouter();
    // @ts-ignore
    const { signUp, setActive, isLoaded } = useSignUp();

    const [username, setUsername] = useState('');
    const [firstName, setFirstName] = useState('');
    const [lastName, setLastName] = useState('');
    const [phoneNumber, setPhoneNumber] = useState('');
    const [step, setStep] = useState(1); // 1: Profile Info, 2: Bank Statement
    const [statementFile, setStatementFile] = useState<DocumentPicker.DocumentPickerAsset | null>(null);
    const [loading, setLoading] = useState(false);
    const { getToken, isSignedIn } = useAuth();
    const { user: clerkUser, isLoaded: userLoaded } = useUser();
    const [alertConfig, setAlertConfig] = useState<{ visible: boolean; title: string; message: string }>({
        visible: false,
        title: '',
        message: '',
    });

    useEffect(() => {
        if (isLoaded && signUp) {
            setFirstName(signUp.firstName || '');
            setLastName(signUp.lastName || '');
        } else if (userLoaded && clerkUser) {
            setFirstName(clerkUser.firstName || '');
            setLastName(clerkUser.lastName || '');
            setUsername(clerkUser.username || '');
            setPhoneNumber(clerkUser.primaryPhoneNumber?.phoneNumber || '');
        }
    }, [isLoaded, signUp, userLoaded, clerkUser]);

    const pickDocument = async () => {
        try {
            const result = await DocumentPicker.getDocumentAsync({
                type: ['text/csv', 'text/comma-separated-values', 'application/csv'],
                copyToCacheDirectory: true,
            });

            if (!result.canceled && result.assets && result.assets.length > 0) {
                setStatementFile(result.assets[0]);
            }
        } catch (err) {
            console.error('Error picking document:', err);
        }
    };

    const onCompleteProfilePress = async () => {
        if (!username || !firstName || !lastName || !phoneNumber) {
            setAlertConfig({ visible: true, title: 'Error', message: 'Please fill in all mandatory fields (Name, Username, Phone)' });
            return;
        }

        if (!isLoaded && !userLoaded) return;
        setLoading(true);

        try {
            if (!isSignedIn && signUp) {
                // In signup flow
                await signUp.update({
                    username,
                    firstName,
                    lastName,
                });

                if (signUp.status === 'complete') {
                    await setActive({ session: signUp.createdSessionId });
                    const token = await getToken();
                    if (token) {
                        await syncUser(token, {
                            clerkId: signUp.createdUserId!,
                            username,
                            firstName,
                            lastName,
                            phoneNumber,
                        });
                    }
                    setStep(2); // Move to CSV step
                }
            } else if (isSignedIn && clerkUser) {
                // Already signed in, update info
                try {
                    await clerkUser.update({
                        firstName,
                        lastName,
                    });
                } catch (clerkError) {
                    console.warn('Clerk update failed (might be non-critical):', clerkError);
                }
                
                const token = await getToken();
                if (token) {
                    await syncUser(token, {
                        clerkId: clerkUser.id,
                        email: clerkUser.primaryEmailAddress?.emailAddress,
                        firstName,
                        lastName,
                        username,
                        phoneNumber,
                    });
                }
                setStep(2); // Move to CSV step
            }
        } catch (err: any) {
            console.error('Profile completion error:', JSON.stringify(err, null, 2));
            setAlertConfig({
                visible: true,
                title: 'Error',
                message: err.errors?.[0]?.message || 'Failed to update profile'
            });
        } finally {
            setLoading(false);
        }
    };

    const onFinishOnboarding = async () => {
        if (statementFile) {
            setLoading(true);
            try {
                const formData = new FormData();
                formData.append('file', {
                    uri: statementFile.uri,
                    name: statementFile.name,
                    type: statementFile.mimeType || 'text/csv',
                } as any);
                await api.uploadFile('/ml/upload-statement/', formData);
                console.log('File uploaded successfully');
            } catch (error) {
                console.error('Upload failed:', error);
                setAlertConfig({ visible: true, title: 'Upload Failed', message: 'Could not process CSV, but your profile is saved.' });
            } finally {
                setLoading(false);
            }
        }
        router.replace('/dashboard');
    };

    if (!isLoaded && !userLoaded) {
        return (
            <View style={styles.loadingContainer}>
                <ActivityIndicator size="large" color="#F97316" />
                <Text style={styles.loadingText}>Preparing setup...</Text>
            </View>
        );
    }

    return (
        <KeyboardAvoidingView
            behavior={Platform.OS === 'ios' ? 'padding' : 'height'}
            style={styles.keyboardAvoidingView}
        >
            <ScrollView
                contentContainerStyle={styles.scrollContent}
                showsVerticalScrollIndicator={false}
            >
                <Animated.View
                    entering={FadeInDown.duration(600).springify()}
                    style={styles.formContainer}
                >
                    {step === 1 ? (
                        <>
                            <Text style={styles.title}>Basic Information</Text>
                            <Text style={styles.subtitle}>
                                Step 1: Basic Information
                            </Text>

                            <View style={styles.inputGroup}>
                                <Text style={styles.label}>Username</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="johndoe123"
                                    placeholderTextColor="#666"
                                    value={username}
                                    onChangeText={setUsername}
                                    autoCapitalize="none"
                                />
                            </View>

                            <View style={styles.row}>
                                <View style={[styles.inputGroup, { flex: 1 }]}>
                                    <Text style={styles.label}>First Name</Text>
                                    <TextInput
                                        style={styles.input}
                                        placeholder="John"
                                        placeholderTextColor="#666"
                                        value={firstName}
                                        onChangeText={setFirstName}
                                    />
                                </View>
                                <View style={[styles.inputGroup, { flex: 1 }]}>
                                    <Text style={styles.label}>Last Name</Text>
                                    <TextInput
                                        style={styles.input}
                                        placeholder="Doe"
                                        placeholderTextColor="#666"
                                        value={lastName}
                                        onChangeText={setLastName}
                                    />
                                </View>
                            </View>

                            <View style={styles.inputGroup}>
                                <Text style={styles.label}>Phone Number</Text>
                                <TextInput
                                    style={styles.input}
                                    placeholder="+91 9876543210"
                                    placeholderTextColor="#666"
                                    value={phoneNumber}
                                    onChangeText={setPhoneNumber}
                                    keyboardType="phone-pad"
                                />
                            </View>

                            <TouchableOpacity
                                onPress={onCompleteProfilePress}
                                disabled={loading}
                                activeOpacity={0.8}
                            >
                                <LinearGradient
                                    colors={['#F97316', '#FB923C']}
                                    start={{ x: 0, y: 0 }}
                                    end={{ x: 1, y: 0 }}
                                    style={styles.button}
                                >
                                    {loading ? (
                                        <ActivityIndicator color="#000" />
                                    ) : (
                                        <Text style={styles.buttonText}>Continue</Text>
                                    )}
                                </LinearGradient>
                            </TouchableOpacity>
                        </>
                    ) : (
                        <>
                            <Text style={styles.title}>Bank Statement</Text>
                            <Text style={styles.subtitle}>
                                Do you want to upload your bank statement? We can automatically categorize your last 6 months of transactions.
                            </Text>

                            <View style={styles.inputGroup}>
                                <TouchableOpacity
                                    style={styles.fileButton}
                                    onPress={pickDocument}
                                    activeOpacity={0.7}
                                >
                                    <Text style={styles.fileButtonText}>
                                        {statementFile ? statementFile.name : 'Select CSV File (Optional)'}
                                    </Text>
                                </TouchableOpacity>
                                {statementFile && (
                                    <Text style={styles.fileHelpText}>
                                        Ready to categorize {statementFile.name}
                                    </Text>
                                )}
                            </View>

                            <TouchableOpacity
                                onPress={onFinishOnboarding}
                                disabled={loading}
                                activeOpacity={0.8}
                                style={{ marginTop: 24 }}
                            >
                                <LinearGradient
                                    colors={statementFile ? ['#F97316', '#FB923C'] : ['#3A3A3C', '#2C2C2E']}
                                    start={{ x: 0, y: 0 }}
                                    end={{ x: 1, y: 0 }}
                                    style={styles.button}
                                >
                                    {loading ? (
                                        <ActivityIndicator color="#fff" />
                                    ) : (
                                        <Text style={[styles.buttonText, { color: statementFile ? '#000' : '#fff' }]}>
                                            {statementFile ? 'Upload and Finish' : 'Skip and Finish'}
                                        </Text>
                                    )}
                                </LinearGradient>
                            </TouchableOpacity>
                        </>
                    )}

                </Animated.View>
            </ScrollView>
            <CustomAlert
                visible={alertConfig.visible}
                title={alertConfig.title}
                message={alertConfig.message}
                onClose={() => setAlertConfig({ ...alertConfig, visible: false })}
            />
        </KeyboardAvoidingView>
    );
}

const styles = StyleSheet.create({
    loadingContainer: {
        flex: 1,
        justifyContent: 'center',
        alignItems: 'center',
        backgroundColor: '#0F172A',
    },
    loadingText: {
        color: '#94A3B8',
        marginTop: 16,
        fontSize: 16,
    },
    keyboardAvoidingView: {
        flex: 1,
    },
    scrollContent: {
        flexGrow: 1,
        justifyContent: 'center',
        padding: 24,
    },
    formContainer: {
        width: '100%',
        backgroundColor: '#1C1C1E',
        borderRadius: 24,
        padding: 24,
        shadowColor: "#000",
        shadowOffset: {
            width: 0,
            height: 4,
        },
        shadowOpacity: 0.25,
        shadowRadius: 8,
        elevation: 8,
    },
    title: {
        fontSize: 32,
        fontWeight: 'bold',
        color: '#fff',
        marginBottom: 8,
    },
    subtitle: {
        fontSize: 14,
        color: '#ccc',
        marginBottom: 32,
        lineHeight: 20,
    },
    inputGroup: {
        marginBottom: 20,
    },
    row: {
        flexDirection: 'row',
        gap: 16,
    },
    label: {
        color: '#ccc',
        marginBottom: 8,
        fontSize: 14,
    },
    input: {
        backgroundColor: '#3A3A3C',
        borderRadius: 12,
        height: 52,
        paddingHorizontal: 16,
        color: '#fff',
        borderWidth: 1,
        borderColor: '#333',
    },
    button: {
        height: 56,
        borderRadius: 28,
        justifyContent: 'center',
        alignItems: 'center',
        marginTop: 16,
        marginBottom: 32,
    },
    buttonText: {
        color: '#000',
        fontWeight: 'bold',
        fontSize: 16,
    },
    fileButton: {
        backgroundColor: '#2C2C2E',
        borderRadius: 12,
        height: 52,
        justifyContent: 'center',
        paddingHorizontal: 16,
        borderWidth: 1,
        borderColor: '#333',
        borderStyle: 'dashed',
    },
    fileButtonText: {
        color: '#F97316',
        fontSize: 14,
        textAlign: 'center',
    },
    fileHelpText: {
        color: '#34C759',
        fontSize: 12,
        marginTop: 6,
        textAlign: 'center',
    },
});
