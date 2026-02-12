
import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

async function getAuthToken(): Promise<string> {
    const { data: { session } } = await supabase.auth.getSession();
    if (!session) {
        throw new Error('No active session');
    }
    return session.access_token;
}

export interface PyqQuestion {
    id: string;
    paper_id: string;
    question_text: string;
    options: any[]; // JSON structure
    correct_answer: string;
    has_image: boolean;
    image_url: string | null;
    subject_id: string;
    chapter_id: string | null;
    topic_id: string | null;
    chapter_ids: string[] | null;
    topic_ids: string[] | null;
    page_number: number;
    question_number: number;
}

export const pyqApi = {
    getHierarchy: async () => {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/api/pyq/hierarchy`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch hierarchy');
        return response.json();
    },

    getQuestions: async (filters: { subject_id?: string; chapter_id?: string; topic_id?: string }) => {
        const token = await getAuthToken();
        const params = new URLSearchParams();
        if (filters.subject_id) params.append('subject_id', filters.subject_id);
        if (filters.chapter_id) params.append('chapter_id', filters.chapter_id);
        if (filters.topic_id) params.append('topic_id', filters.topic_id);

        const response = await fetch(`${API_BASE_URL}/api/pyq/questions?${params.toString()}`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch questions');
        return response.json() as Promise<PyqQuestion[]>;
    },

    getPapers: async () => {
        const token = await getAuthToken();
        const response = await fetch(`${API_BASE_URL}/api/pyq/papers`, {
            headers: {
                'Authorization': `Bearer ${token}`
            }
        });
        if (!response.ok) throw new Error('Failed to fetch papers');
        return response.json();
    }
};
