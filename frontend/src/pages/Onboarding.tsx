import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '@/hooks/useAuth';
import { supabase } from '@/integrations/supabase/client';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { Progress } from '@/components/ui/progress';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Logo } from '@/components/ui/Logo';
import { AlertCircle, Loader2, ChevronRight, ChevronLeft } from 'lucide-react';
import { toast } from 'sonner';
import { Grade } from '@/types';

interface OnboardingData {
  email: string;
  password: string;
  confirmPassword: string;
  name: string;
  phone: string;
  grade: Grade | '';
  syllabus: 'cbse' | 'icse' | 'state' | '';
  targetExam: string;
  focusSubjects: string[];
}

const STEPS = ['Account', 'Personal Info', 'Academic', 'Goals'];

export default function Onboarding() {
  const navigate = useNavigate();
  const { signUp, user } = useAuth();
  const [step, setStep] = useState(0);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const [data, setData] = useState<OnboardingData>({
    email: '',
    password: '',
    confirmPassword: '',
    name: '',
    phone: '',
    grade: '',
    syllabus: '',
    targetExam: 'jee-main',
    focusSubjects: [],
  });

  const progress = ((step + 1) / STEPS.length) * 100;

  // Force dark mode to match main app
  useEffect(() => {
    document.documentElement.classList.add("dark");
  }, []);

  useEffect(() => {
    // If we have a user from elsewhere, we can pre-populate
    if (user && step === 0) {
      setStep(1);
      if (user.email) {
        setData(prev => ({ ...prev, email: user.email! }));
      }
    }
  }, [user, step]);

  const updateData = (field: keyof OnboardingData, value: any) => {
    setData((prev) => ({ ...prev, [field]: value }));
    setError('');
  };

  const validateStep = () => {
    switch (step) {
      case 0: // Account
        if (!data.email || !data.password || !data.confirmPassword) {
          setError('Please fill in all fields');
          return false;
        }
        if (data.password.length < 6) {
          setError('Password must be at least 6 characters');
          return false;
        }
        if (data.password !== data.confirmPassword) {
          setError('Passwords do not match');
          return false;
        }
        return true;
      case 1: // Personal
        if (!data.name) {
          setError('Please enter your name');
          return false;
        }
        return true;
      case 2: // Academic
        if (!data.grade || !data.syllabus) {
          setError('Please select your grade and syllabus');
          return false;
        }
        return true;
      case 3: // Goals
        if (!data.targetExam) {
          setError('Please select your target exam');
          return false;
        }
        return true;
      default:
        return true;
    }
  };

  const handleNext = async () => {
    if (!validateStep()) return;

    if (step === 0) {
      // Create auth account via Backend (auto-confirms email)
      setLoading(true);

      try {
        const response = await fetch(`${import.meta.env.VITE_API_BASE_URL}/auth/signup`, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email: data.email,
            password: data.password,
          }),
        });

        const result = await response.json();

        if (!response.ok) {
          throw new Error(result.detail || 'Signup failed');
        }

        // Account created and confirmed. Now sign in immediately.
        const { error: signInError } = await supabase.auth.signInWithPassword({
          email: data.email,
          password: data.password,
        });

        if (signInError) {
          throw signInError;
        }

        toast.success('Account created successfully!');

      } catch (err: any) {
        setLoading(false);
        // Handle "User already registered" specifically if needed, otherwise generic error
        if (err.message.includes("User already registered")) {
          setError("This email is already registered. Please sign in.");
        } else {
          setError(err.message);
        }
        return;
      }

      setLoading(false);
    }

    if (step === STEPS.length - 1) {
      // Final step - update profile with collected data
      await handleComplete();
    } else {
      setStep((prev) => prev + 1);
    }
  };

  const handleComplete = async () => {
    setLoading(true);

    try {
      // Get the current user
      const { data: { user: currentUser } } = await supabase.auth.getUser();

      if (!currentUser) {
        throw new Error('No authenticated user found. Please try signing in manually.');
      }

      // Update user profile (trigger already created it, we just update with onboarding data)
      const profileUpdate = {
        name: data.name,
        phone: data.phone || null,
        grade: data.grade as any,
        syllabus: data.syllabus as any,
        target_exam: data.targetExam,
      };

      const { error: profileError } = await (supabase as any)
        .from('users')
        .update(profileUpdate)
        .eq('id', currentUser.id);

      if (profileError) throw profileError;

      // Update user preferences (trigger already created it)
      const preferencesUpdate = {
        focus_subjects: data.focusSubjects as any,
        daily_goal: 20,
        difficulty_level: 'adaptive' as any,
      };

      const { error: preferencesError } = await (supabase as any)
        .from('user_preferences')
        .update(preferencesUpdate)
        .eq('user_id', currentUser.id);

      if (preferencesError) throw preferencesError;

      toast.success('Welcome to Catalyst! Your account is ready.');
      navigate('/dashboard', { replace: true });
    } catch (err: any) {
      console.error('Onboarding error:', err);
      setError(err.message || 'Failed to complete onboarding');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep((prev) => Math.max(0, prev - 1));
    setError('');
  };

  const toggleSubject = (subject: string) => {
    setData((prev) => ({
      ...prev,
      focusSubjects: prev.focusSubjects.includes(subject)
        ? prev.focusSubjects.filter((s) => s !== subject)
        : [...prev.focusSubjects, subject],
    }));
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <Card className="w-full max-w-2xl shadow-xl border-border animate-fade-in">
        <CardHeader className="space-y-1 text-center pb-6">
          <div className="flex justify-center mb-4">
            <div className="h-16 w-16 rounded-xl bg-primary/10 flex items-center justify-center ring-1 ring-primary/20">
              <Logo size="md" />
            </div>
          </div>
          <CardTitle className="text-3xl font-bold text-foreground">Welcome to Catalyst</CardTitle>
          <CardDescription className="text-base text-muted-foreground">
            Step {step + 1} of {STEPS.length}: {STEPS[step]}
          </CardDescription>
          <Progress value={progress} className="mt-4 h-2" />
        </CardHeader>

        <CardContent className="space-y-6">
          {error && (
            <Alert variant="destructive" className="animate-slide-down">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          )}

          {/* Step 0: Account Creation */}
          {step === 0 && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <Label htmlFor="email" className="text-foreground">Email</Label>
                <Input
                  id="email"
                  type="email"
                  placeholder="student@example.com"
                  value={data.email}
                  onChange={(e) => updateData('email', e.target.value)}
                  disabled={loading}
                  className="h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="password" className="text-foreground">Password</Label>
                <Input
                  id="password"
                  type="password"
                  placeholder="At least 6 characters"
                  value={data.password}
                  onChange={(e) => updateData('password', e.target.value)}
                  disabled={loading}
                  className="h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="confirmPassword" className="text-foreground">Confirm Password</Label>
                <Input
                  id="confirmPassword"
                  type="password"
                  placeholder="Re-enter your password"
                  value={data.confirmPassword}
                  onChange={(e) => updateData('confirmPassword', e.target.value)}
                  disabled={loading}
                  className="h-11"
                />
              </div>
            </div>
          )}

          {/* Step 1: Personal Details */}
          {step === 1 && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <Label htmlFor="name" className="text-foreground">Full Name</Label>
                <Input
                  id="name"
                  type="text"
                  placeholder="Enter your full name"
                  value={data.name}
                  onChange={(e) => updateData('name', e.target.value)}
                  disabled={loading}
                  className="h-11"
                />
              </div>
              <div className="space-y-2">
                <Label htmlFor="phone" className="text-foreground">Phone Number (Optional)</Label>
                <Input
                  id="phone"
                  type="tel"
                  placeholder="Enter your phone number"
                  value={data.phone}
                  onChange={(e) => updateData('phone', e.target.value)}
                  disabled={loading}
                  className="h-11"
                />
              </div>
            </div>
          )}

          {/* Step 2: Academic */}
          {step === 2 && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <Label htmlFor="grade" className="text-foreground">Grade</Label>
                <Select
                  value={data.grade}
                  onValueChange={(value) => updateData('grade', value)}
                  disabled={loading}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Select your grade" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="9">Grade 9</SelectItem>
                    <SelectItem value="10">Grade 10</SelectItem>
                    <SelectItem value="11">Grade 11</SelectItem>
                    <SelectItem value="12">Grade 12</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label htmlFor="syllabus" className="text-foreground">Syllabus</Label>
                <Select
                  value={data.syllabus}
                  onValueChange={(value) => updateData('syllabus', value)}
                  disabled={loading}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Select your syllabus" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cbse">CBSE</SelectItem>
                    <SelectItem value="icse">ICSE</SelectItem>
                    <SelectItem value="state">State Board</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          )}

          {/* Step 3: Goals */}
          {step === 3 && (
            <div className="space-y-4 animate-fade-in">
              <div className="space-y-2">
                <Label htmlFor="targetExam" className="text-foreground">Target Exam</Label>
                <Select
                  value={data.targetExam}
                  onValueChange={(value) => updateData('targetExam', value)}
                  disabled={loading}
                >
                  <SelectTrigger className="h-11">
                    <SelectValue placeholder="Select your target exam" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="jee-main">JEE Main</SelectItem>
                    <SelectItem value="jee-advanced">JEE Advanced</SelectItem>
                    <SelectItem value="both">Both JEE Main & Advanced</SelectItem>
                    <SelectItem value="neet">NEET</SelectItem>
                    <SelectItem value="boards">Board Exams</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div className="space-y-2">
                <Label className="text-foreground">Focus Subjects (Optional)</Label>
                <div className="grid grid-cols-3 gap-3">
                  {['Physics', 'Chemistry', 'Mathematics'].map((subject) => (
                    <Button
                      key={subject}
                      type="button"
                      variant={data.focusSubjects.includes(subject.toLowerCase()) ? 'default' : 'outline'}
                      className="w-full h-11"
                      onClick={() => toggleSubject(subject.toLowerCase())}
                      disabled={loading}
                    >
                      {subject}
                    </Button>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Navigation Buttons */}
          <div className="flex justify-between pt-6 border-t border-border/50">
            <Button
              type="button"
              variant="outline"
              onClick={handleBack}
              disabled={step === 0 || loading}
              className="h-11 px-6"
            >
              <ChevronLeft className="mr-2 h-4 w-4" />
              Back
            </Button>
            <Button onClick={handleNext} disabled={loading} className="h-11 px-6">
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  {step === STEPS.length - 1 ? 'Completing...' : 'Processing...'}
                </>
              ) : step === STEPS.length - 1 ? (
                'Complete'
              ) : (
                <>
                  Next
                  <ChevronRight className="ml-2 h-4 w-4" />
                </>
              )}
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
