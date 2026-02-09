import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

export interface TestCreateRequest {
    title: string;
    type: string;
    subject?: string;
    subject_id?: string;
    duration: number;
    number_of_questions?: number;
    chapter_ids?: string[];
    topic_ids?: string[];
    difficulty?: string;
    schedule_at?: string;
}

export const testApi = {
    createTest: async (data: TestCreateRequest) => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch(`${API_BASE_URL}/api/tests/create`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });

        if (!response.ok) {
            const err = await response.json();
            throw new Error(err.detail || 'Failed to create test');
        }

        return response.json();
    },

    getTests: async () => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch(`${API_BASE_URL}/api/tests/`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch tests');
        return response.json();
    },

    getTest: async (id: string) => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch(`${API_BASE_URL}/api/tests/${id}`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch test');
        return response.json();
    },

    submitTest: async (data: any) => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch(`${API_BASE_URL}/api/tests/submit`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${token}`
            },
            body: JSON.stringify(data)
        });
        if (!response.ok) throw new Error('Failed to submit test');
        return response.json();
    },

    getHierarchy: async () => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch(`${API_BASE_URL}/api/analysis/hierarchy`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch hierarchy');
        return response.json();
    },

    getTestResults: async (testId: string) => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch(`${API_BASE_URL}/api/tests/${testId}/results`, {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch test results');
        return response.json();
    }
};
