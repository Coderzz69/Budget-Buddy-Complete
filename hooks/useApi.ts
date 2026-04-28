import { useAuth } from '@clerk/expo';
import axios from 'axios';
import { useMemo } from 'react';
import { Account, Budget, Category, Transaction } from '../store/useStore';

const API_URL = process.env.EXPO_PUBLIC_API_URL || 'http://localhost:8000/api';

export interface SpikeInsight {
  category: string;
  increase: number;
}

export interface CategoryBreakdown {
  category: string;
  amount: number;
  percentage: number;
}

export interface InsightCard {
  id: string;
  kind: string;
  title: string;
  message: string;
  tone: 'info' | 'success' | 'warning' | 'danger';
  amount?: number;
  footer?: string;
}

export interface InsightsMonthlyResponse {
  total_spent: number;
  previous_total: number;
  percent_change: number;
  top_categories: CategoryBreakdown[];
  spikes: SpikeInsight[];
  insight_cards: InsightCard[];
  top_category: string | null;
  savings_hint?: string;
}

export interface MLPredictionResponse {
  predicted_category: string;
  confidence: number;
  alternatives: { category: string; confidence: number }[];
}

export interface MLSummaryResponse {
  summary: any;
}

export const useApi = () => {
  const { getToken } = useAuth();
  
  const api = useMemo(() => {
    const instance = axios.create({
      baseURL: API_URL,
    });
    
    instance.interceptors.request.use(async (config) => {
      try {
        const token = await getToken();
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
      } catch (e) {
        console.error('Error fetching token for API request', e);
      }
      return config;
    });
    
    return instance;
  }, [getToken]);
  
  return useMemo(() => ({
    syncUser: async (clerkId: string, email: string, name?: string, profilePic?: string) => {
      return api.post('/auth/sync-user/', { clerkId, email, name, profilePic });
    },

    // Accounts
    getAccounts: async () => api.get<Account[]>('/accounts/'),
    createAccount: async (data: Omit<Account, 'id'>) => api.post<Account>('/accounts/', data),
    updateAccount: async (id: string, data: Partial<Account>) => api.patch<Account>(`/accounts/${id}/`, data),
    deleteAccount: async (id: string) => api.delete(`/accounts/${id}/`),

    // Categories
    getCategories: async () => api.get<Category[]>('/categories/'),
    createCategory: async (data: Omit<Category, 'id'>) => api.post<Category>('/categories/', data),
    updateCategory: async (id: string, data: Partial<Category>) => api.patch<Category>(`/categories/${id}/`, data),
    deleteCategory: async (id: string) => api.delete(`/categories/${id}/`),

    // Transactions
    getTransactions: async (params?: any) => api.get<{ count: number, results: Transaction[] }>('/transactions/', { params }),
    createTransaction: async (data: any) => api.post<Transaction>('/transactions/', data),
    updateTransaction: async (id: string, data: any) => api.patch<Transaction>(`/transactions/${id}/`, data),
    deleteTransaction: async (id: string) => api.delete(`/transactions/${id}/`),

    // Budgets
    getBudgets: async () => api.get<Budget[]>('/budgets/'),
    createBudget: async (data: any) => api.post<Budget>('/budgets/', data),
    updateBudget: async (id: string, data: any) => api.patch<Budget>(`/budgets/${id}/`, data),
    deleteBudget: async (id: string) => api.delete(`/budgets/${id}/`),

    // Dashboard Summary
    getDashboardSummary: async () => api.get('/dashboard/'),

    // Insights
    getMonthlyInsights: async (month: string) =>
      api.get<InsightsMonthlyResponse>('/insights/', { params: { month } }),
      
    // ML Services
    getMLSummary: async () => api.get<MLSummaryResponse>('/ml/summary/'),
    predictCategory: async (note: string, amount: number) => 
      api.post<MLPredictionResponse>('/ml/categorize/', { note, amount }),
  }), [api]);
};
