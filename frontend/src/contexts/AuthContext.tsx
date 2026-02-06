import { createContext, useContext, useEffect, useState } from 'react';
import { User, Session } from '@supabase/supabase-js';
import { supabase } from '@/integrations/supabase/client';
import { Database } from '@/integrations/supabase/types';
import { MigrationService } from '@/services/migrationService';

type UserProfile = Database['public']['Tables']['users']['Row'];

interface AuthContextType {
  user: User | null;
  profile: UserProfile | null;
  session: Session | null;
  loading: boolean;
  signUp: (email: string, password: string) => Promise<{ error: any }>;
  signIn: (email: string, password: string) => Promise<{ error: any }>;
  signOut: () => Promise<void>;
  resetPassword: (email: string) => Promise<{ error: any }>;
  updateProfile: (data: Partial<UserProfile>) => Promise<{ error: any }>;
  refreshProfile: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const AuthProvider = ({ children }: { children: React.ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [profile, setProfile] = useState<UserProfile | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchProfile = async (userId: string) => {
    console.log('🔍 [AuthContext] Starting profile fetch for user:', userId);
    try {
      // Small delay to ensure auth session is fully established
      await new Promise(resolve => setTimeout(resolve, 100));

      console.log('🔍 [AuthContext] Querying users table...');
      const { data, error } = await supabase
        .from('users')
        .select('*')
        .eq('id', userId)
        .single();

      if (error) {
        console.error('❌ [AuthContext] Error fetching profile:', {
          code: error.code,
          message: error.message,
          details: error.details,
          hint: error.hint
        });
        // If it's a 401 or PGRST116 (not found), the profile might not exist yet
        if (error.code === 'PGRST116') {
          console.warn('⚠️ [AuthContext] Profile not found - user needs to complete onboarding');
          setProfile(null);
        } else {
          // For other errors, retry once after a delay
          console.log('🔄 [AuthContext] Retrying profile fetch in 500ms...');
          await new Promise(resolve => setTimeout(resolve, 500));
          const { data: retryData, error: retryError } = await supabase
            .from('users')
            .select('*')
            .eq('id', userId)
            .single();

          if (retryError) {
            console.error('❌ [AuthContext] Retry failed:', {
              code: retryError.code,
              message: retryError.message
            });
            setProfile(null);
          } else {
            setProfile(retryData);
          }
        }
      } else {
        console.log('✅ [AuthContext] Profile fetched successfully:', data);
        setProfile(data);

        // Run migration if needed (only runs once)
        if (!MigrationService.isMigrationCompleted()) {
          // Run in background without blocking
          MigrationService.runWithNotification().catch(err => {
            console.error('Migration error:', err);
          });
        }
      }
    } catch (error) {
      console.error('❌ [AuthContext] Unexpected error fetching profile:', error);
      setProfile(null);
    } finally {
      console.log('🏁 [AuthContext] Profile fetch complete. Loading = false');
      setLoading(false);
    }
  };

  useEffect(() => {
    let isMounted = true;
    let fetchTimeout: NodeJS.Timeout | null = null;
    let authSubscription: any = null;

    // Get initial session
    supabase.auth.getSession().then(({ data: { session } }) => {
      if (!isMounted) return;

      setSession(session);
      setUser(session?.user ?? null);
      if (session?.user) {
        fetchProfile(session.user.id);
      } else {
        setLoading(false);
      }
    });

    // Listen for auth changes
    const setupAuthListener = () => {
      const {
        data: { subscription },
      } = supabase.auth.onAuthStateChange((event, session) => {
        if (!isMounted) return;

        console.log("Auth state change:", event);

        // Ignore TOKEN_REFRESHED and USER_UPDATED events to prevent unnecessary reloads
        if (event === 'TOKEN_REFRESHED' || event === 'USER_UPDATED') {
          // Just update the session without triggering profile refetch
          setSession(session);
          return;
        }

        // Clear any pending fetch timeout
        if (fetchTimeout) {
          clearTimeout(fetchTimeout);
          fetchTimeout = null;
        }

        setSession(session);
        setUser(session?.user ?? null);

        if (session?.user) {
          // Set loading state for sign-in events
          if (event === 'SIGNED_IN' || event === 'INITIAL_SESSION') {
            setLoading(true);
          }

          // Debounce profile fetches to prevent multiple rapid calls
          fetchTimeout = setTimeout(() => {
            if (isMounted) {
              fetchProfile(session.user.id);
            }
          }, 200);
        } else if (event === 'SIGNED_OUT') {
          // Only clear profile on explicit sign out
          setProfile(null);
          setLoading(false);
        }
      });

      authSubscription = subscription;
    };

    setupAuthListener();

    // Prevent page unload/visibility changes from affecting state
    const handleVisibilityChange = () => {
      // Don't do anything on visibility change - keep state intact
      console.log('Visibility changed:', document.hidden ? 'hidden' : 'visible');
    };

    document.addEventListener('visibilitychange', handleVisibilityChange);

    return () => {
      isMounted = false;
      if (fetchTimeout) {
        clearTimeout(fetchTimeout);
      }
      if (authSubscription) {
        authSubscription.unsubscribe();
      }
      document.removeEventListener('visibilitychange', handleVisibilityChange);
    };
  }, []);

  const signUp = async (email: string, password: string) => {
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: window.location.origin,
      },
    });
    return { data, error };
  };

  const signIn = async (email: string, password: string) => {
    const { error } = await supabase.auth.signInWithPassword({
      email,
      password,
    });
    return { error };
  };

  const signOut = async () => {
    await supabase.auth.signOut();
    setProfile(null);
  };

  const resetPassword = async (email: string) => {
    const { error } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/reset-password`,
    });
    return { error };
  };

  const updateProfile = async (data: Partial<UserProfile>) => {
    if (!user) return { error: new Error('No user logged in') };

    // Sanitize data to prevent updating restricted fields like role
    const { role: _role, created_at: _created_at, updated_at: _updated_at, id: _id, ...updates } = data;

    // Use 'any' cast on the query builder to bypass inference issue where update() expects 'never'
    const { error } = await (supabase.from('users') as any)
      .update(updates)
      .eq('id', user.id);

    if (!error && profile) {
      setProfile({ ...profile, ...data });
    }

    return { error };
  };

  const refreshProfile = async () => {
    if (user) {
      await fetchProfile(user.id);
    }
  };

  const value = {
    user,
    profile,
    session,
    loading,
    signUp,
    signIn,
    signOut,
    resetPassword,
    updateProfile,
    refreshProfile,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};
