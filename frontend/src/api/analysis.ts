import { supabase } from '@/integrations/supabase/client';

export const analysisApi = {
    getPerformanceTrend: async (subject?: string, days = 30) => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const url = new URL('/api/analysis/performance-trend', window.location.origin);
        if (subject) url.searchParams.append('subject', subject);
        url.searchParams.append('days', days.toString());

        const response = await fetch(url.toString(), {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch performance trend');
        return response.json();
    },

    getTopicBreakdown: async (subject: string) => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const url = new URL('/api/analysis/topic-breakdown', window.location.origin);
        url.searchParams.append('subject', subject);

        const response = await fetch(url.toString(), {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch topic breakdown');
        return response.json();
    },

    getWeakAreas: async () => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch('/api/analysis/weak-areas-analysis', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch weak areas');
        return response.json();
    },

    getSubjectComparison: async () => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch('/api/analysis/subject-comparison', {
            headers: { 'Authorization': `Bearer ${token}` }
        });

        if (!response.ok) throw new Error('Failed to fetch subject comparison');
        return response.json();
    },

    getHierarchy: async () => {
        const { data: { session } } = await supabase.auth.getSession();
        const token = session?.access_token;
        if (!token) throw new Error('No session');

        const response = await fetch('/api/analysis/hierarchy', {
            headers: { 'Authorization': `Bearer ${token}` }
        });
        if (!response.ok) throw new Error('Failed to fetch hierarchy');
        return response.json();
    }
};
