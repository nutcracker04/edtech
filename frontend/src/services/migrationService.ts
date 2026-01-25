import { supabase } from '@/integrations/supabase/client';
import { toast } from 'sonner';

interface LocalStorageData {
  'jee-settings'?: any;
  'jee-performance-data-current-user'?: any;
}

/**
 * Migration service to move data from localStorage to Supabase
 */
export class MigrationService {
  private static MIGRATION_KEY = 'migration-completed';

  /**
   * Check if migration has already been completed
   */
  static isMigrationCompleted(): boolean {
    return localStorage.getItem(this.MIGRATION_KEY) === 'true';
  }

  /**
   * Mark migration as completed
   */
  static markMigrationCompleted(): void {
    localStorage.setItem(this.MIGRATION_KEY, 'true');
  }

  /**
   * Get all localStorage data that needs migration
   */
  private static getLocalStorageData(): LocalStorageData {
    const data: LocalStorageData = {};
    
    // Get settings
    const settings = localStorage.getItem('jee-settings');
    if (settings) {
      try {
        data['jee-settings'] = JSON.parse(settings);
      } catch (e) {
        console.error('Failed to parse settings:', e);
      }
    }

    // Get performance data
    const performanceData = localStorage.getItem('jee-performance-data-current-user');
    if (performanceData) {
      try {
        data['jee-performance-data-current-user'] = JSON.parse(performanceData);
      } catch (e) {
        console.error('Failed to parse performance data:', e);
      }
    }

    return data;
  }

  /**
   * Migrate user preferences to Supabase
   */
  private static async migratePreferences(userId: string, settings: any): Promise<void> {
    if (!settings) return;

    // Check if preferences already exist
    const { data: existing } = await supabase
      .from('user_preferences')
      .select('id')
      .eq('user_id', userId)
      .single();

    const preferencesData = {
      user_id: userId,
      daily_goal: settings.dailyGoal || 20,
      focus_subjects: settings.focusSubjects || [],
      difficulty_level: settings.difficultyLevel || 'adaptive',
      notifications_enabled: settings.notifications !== false,
      daily_reminders: settings.dailyReminders !== false,
      dark_mode: settings.darkMode || false,
    };

    if (existing) {
      // Update existing preferences
      const { error } = await supabase
        .from('user_preferences')
        .update(preferencesData)
        .eq('user_id', userId);

      if (error) throw error;
    } else {
      // Insert new preferences
      const { error } = await supabase
        .from('user_preferences')
        .insert(preferencesData);

      if (error) throw error;
    }
  }

  /**
   * Migrate topic mastery data to Supabase
   */
  private static async migrateTopicMastery(userId: string, performanceData: any): Promise<void> {
    if (!performanceData || !performanceData.topicMasteries) return;

    const masteries = performanceData.topicMasteries;
    
    for (const mastery of masteries) {
      // Check if this topic mastery already exists
      const { data: existing } = await supabase
        .from('topic_mastery')
        .select('id')
        .eq('user_id', userId)
        .eq('subject', mastery.subject)
        .eq('topic', mastery.topic)
        .single();

      const masteryData = {
        user_id: userId,
        subject: mastery.subject,
        topic: mastery.topic,
        mastery_score: mastery.masteryScore || 0,
        questions_attempted: mastery.questionsAttempted || 0,
        questions_correct: mastery.questionsCorrect || 0,
        last_attempt_date: mastery.lastAttemptDate || new Date().toISOString(),
        trend: mastery.trend || null,
      };

      if (existing) {
        // Update existing mastery
        const { error } = await supabase
          .from('topic_mastery')
          .update(masteryData)
          .eq('id', existing.id);

        if (error) throw error;
      } else {
        // Insert new mastery
        const { error } = await supabase
          .from('topic_mastery')
          .insert(masteryData);

        if (error) throw error;
      }
    }
  }

  /**
   * Migrate test attempts to Supabase
   */
  private static async migrateTestAttempts(userId: string, performanceData: any): Promise<void> {
    if (!performanceData || !performanceData.testAttempts) return;

    const attempts = performanceData.testAttempts;
    
    // Group attempts by test
    const attemptsByTest: { [testId: string]: any[] } = {};
    for (const attempt of attempts) {
      const testId = attempt.testId || 'unknown';
      if (!attemptsByTest[testId]) {
        attemptsByTest[testId] = [];
      }
      attemptsByTest[testId].push(attempt);
    }

    // For each test, check if it exists and create if not
    for (const [testId, testAttempts] of Object.entries(attemptsByTest)) {
      // Check if test exists
      const { data: existingTest } = await supabase
        .from('tests')
        .select('id')
        .eq('id', testId)
        .single();

      // If test doesn't exist, create a placeholder test
      if (!existingTest && testId !== 'unknown') {
        const { error: testError } = await supabase
          .from('tests')
          .insert({
            id: testId,
            user_id: userId,
            title: 'Migrated Test',
            type: 'practice',
            status: 'completed',
            duration: 0,
            questions: [],
          });

        if (testError && testError.code !== '23505') { // Ignore duplicate key errors
          console.error('Failed to create test:', testError);
          continue;
        }
      }

      // Insert attempts
      for (const attempt of testAttempts) {
        const attemptData = {
          test_id: testId,
          user_id: userId,
          question_id: attempt.questionId || `q-${Date.now()}`,
          selected_answer: attempt.selectedAnswer || null,
          is_correct: attempt.isCorrect || false,
          time_spent: attempt.timeSpent || 0,
          marked_for_review: attempt.markedForReview || false,
          created_at: attempt.createdAt || new Date().toISOString(),
        };

        const { error } = await supabase
          .from('test_attempts')
          .insert(attemptData);

        // Ignore duplicate errors
        if (error && error.code !== '23505') {
          console.error('Failed to insert attempt:', error);
        }
      }
    }
  }

  /**
   * Main migration function
   */
  static async migrate(): Promise<{ success: boolean; error?: string }> {
    try {
      // Check if already migrated
      if (this.isMigrationCompleted()) {
        return { success: true };
      }

      // Get current user
      const { data: { user } } = await supabase.auth.getUser();
      if (!user) {
        return { success: false, error: 'No user logged in' };
      }

      // Get localStorage data
      const localData = this.getLocalStorageData();

      // If no data to migrate, mark as completed
      if (Object.keys(localData).length === 0) {
        this.markMigrationCompleted();
        return { success: true };
      }

      console.log('Starting migration...', {
        hasSettings: !!localData['jee-settings'],
        hasPerformance: !!localData['jee-performance-data-current-user'],
      });

      // Migrate preferences
      if (localData['jee-settings']) {
        await this.migratePreferences(user.id, localData['jee-settings']);
      }

      // Migrate topic mastery
      const performanceData = localData['jee-performance-data-current-user'];
      if (performanceData) {
        await this.migrateTopicMastery(user.id, performanceData);
        await this.migrateTestAttempts(user.id, performanceData);
      }

      // Mark migration as completed
      this.markMigrationCompleted();

      console.log('Migration completed successfully');
      return { success: true };
    } catch (error: any) {
      console.error('Migration failed:', error);
      return { success: false, error: error.message };
    }
  }

  /**
   * Run migration with user notification
   */
  static async runWithNotification(): Promise<void> {
    // Only run if not already migrated
    if (this.isMigrationCompleted()) {
      return;
    }

    toast.loading('Migrating your data to cloud storage...');

    const result = await this.migrate();

    toast.dismiss();

    if (result.success) {
      toast.success('Your data has been migrated successfully!');
    } else {
      toast.error(`Migration failed: ${result.error}`, {
        description: 'Some data may not have been migrated. Please contact support if issues persist.',
      });
    }
  }

  /**
   * Clear localStorage data (use after successful migration)
   */
  static clearLocalStorageData(): void {
    // Keep the migration flag
    const migrationFlag = localStorage.getItem(this.MIGRATION_KEY);
    
    localStorage.removeItem('jee-settings');
    localStorage.removeItem('jee-performance-data-current-user');
    
    // Restore migration flag
    if (migrationFlag) {
      localStorage.setItem(this.MIGRATION_KEY, migrationFlag);
    }
  }
}
