import { supabase } from '@/integrations/supabase/client';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

interface ExtractedQuestion {
  question_number: number;
  question_text: string;
  options: Array<{ id: string; text: string }>;
  confidence: number;
  subject?: string;
  topic?: string;
}

interface UploadStatusResponse {
  id: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  progress: number;
  extracted_questions?: ExtractedQuestion[];
  error_message?: string;
}

async function getAuthToken(): Promise<string> {
  const { data: { session } } = await supabase.auth.getSession();
  if (!session) {
    throw new Error('No active session');
  }
  return session.access_token;
}

export const uploadService = {
  /**
   * Upload test paper image for OCR processing
   */
  async uploadTestPaper(file: File): Promise<{ id: string; status: string; message: string }> {
    const token = await getAuthToken();
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload/test-paper`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
  },
  
  /**
   * Check the status of an uploaded test
   */
  async getUploadStatus(uploadId: string): Promise<UploadStatusResponse> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/upload/status/${uploadId}`, {
      headers: {
        'Authorization': `Bearer ${token}`,
      },
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to get status');
    }
    
    return response.json();
  },
  
  /**
   * Confirm extracted questions and create test
   */
  async confirmQuestions(
    uploadId: string,
    questions: any[],
    userAnswers?: Record<number, string>
  ): Promise<{ message: string; test_id: string }> {
    const token = await getAuthToken();
    
    const response = await fetch(`${API_BASE_URL}/api/upload/confirm`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        upload_id: uploadId,
        questions,
        user_answers: userAnswers,
      }),
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Failed to confirm questions');
    }
    
    return response.json();
  },
  
  /**
   * Upload response sheet
   */
  async uploadResponseSheet(uploadId: string, file: File): Promise<{ id: string; status: string; message: string }> {
    const token = await getAuthToken();
    
    const formData = new FormData();
    formData.append('file', file);
    
    const response = await fetch(`${API_BASE_URL}/api/upload/response-sheet?upload_id=${uploadId}`, {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${token}`,
      },
      body: formData,
    });
    
    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Upload failed');
    }
    
    return response.json();
  },
};
