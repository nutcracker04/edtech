import { useState, useEffect } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { User, Bell, BookOpen, Moon, Sun, LogOut, Save, Loader2 } from "lucide-react";
import { Switch } from "@/components/ui/switch";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { GradeSelector, TargetExamSelector } from "@/components/settings/GradeSelector";
import { Grade, TargetExam } from "@/types";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { supabase } from "@/integrations/supabase/client";
import { useAuth } from "@/hooks/useAuth";
import { toast } from "sonner";
import { useNavigate } from "react-router-dom";

const Settings = () => {
  const { signOut } = useAuth();
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);

  // User profile data
  const [name, setName] = useState("");
  const [email, setEmail] = useState("");
  const [phone, setPhone] = useState("");
  const [grade, setGrade] = useState<Grade | null>(null);
  const [syllabus, setSyllabus] = useState<'cbse' | 'icse' | 'state' | ''>('');
  const [targetExam, setTargetExam] = useState<TargetExam | null>(null);

  // Preferences
  const [notifications, setNotifications] = useState(true);
  const [dailyReminders, setDailyReminders] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [dailyGoal, setDailyGoal] = useState("20");
  const [difficultyLevel, setDifficultyLevel] = useState<'easy' | 'adaptive' | 'hard'>("adaptive");
  const [focusSubjects, setFocusSubjects] = useState<string[]>([]);

  const [hasChanges, setHasChanges] = useState(false);

  // Load user data from Supabase
  useEffect(() => {
    loadUserData();
  }, []);

  const loadUserData = async () => {
    try {
      setLoading(true);
      const { data: { user } } = await supabase.auth.getUser();

      if (!user) {
        toast.error("Please sign in to view settings");
        navigate("/login");
        return;
      }

      // Load user profile
      const { data: profile, error: profileError } = await (supabase as any)
        .from('users')
        .select('*')
        .eq('id', user.id)
        .single();

      if (profileError) throw profileError;

      if (profile) {
        setName(profile.name);
        setEmail(profile.email);
        setPhone(profile.phone || '');
        setGrade(profile.grade as Grade);
        setSyllabus(profile.syllabus);
        setTargetExam(profile.target_exam as TargetExam);
      }

      // Load user preferences
      const { data: preferences, error: preferencesError } = await (supabase as any)
        .from('user_preferences')
        .select('*')
        .eq('user_id', user.id)
        .maybeSingle();

      if (preferencesError) {
        throw preferencesError;
      }

      if (preferences) {
        setDailyGoal(preferences.daily_goal?.toString() || '20');
        setFocusSubjects((preferences.focus_subjects as string[]) || []);
        setDifficultyLevel(preferences.difficulty_level as 'easy' | 'adaptive' | 'hard' || 'adaptive');
        setNotifications(preferences.notifications_enabled ?? true);
        setDailyReminders(preferences.daily_reminders ?? true);
        setDarkMode(preferences.dark_mode ?? true);
      }

    } catch (error: any) {
      console.error('Error loading user data:', error);
      toast.error('Failed to load settings');
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      const { data: { user } } = await supabase.auth.getUser();

      if (!user) {
        toast.error("Please sign in to save settings");
        return;
      }

      // Update user profile
      const { error: profileError } = await (supabase as any)
        .from('users')
        .update({
          name,
          phone: phone || null,
          grade,
          syllabus,
          target_exam: targetExam,
        })
        .eq('id', user.id);

      if (profileError) throw profileError;

      // Update or insert user preferences
      const { error: preferencesError } = await (supabase as any)
        .from('user_preferences')
        .upsert({
          user_id: user.id,
          daily_goal: parseInt(dailyGoal),
          focus_subjects: focusSubjects,
          difficulty_level: difficultyLevel,
          notifications_enabled: notifications,
          daily_reminders: dailyReminders,
          dark_mode: darkMode,
        }, {
          onConflict: 'user_id'
        });

      if (preferencesError) throw preferencesError;

      toast.success('Settings saved successfully!');
      setHasChanges(false);
    } catch (error: any) {
      console.error('Error saving settings:', error);
      toast.error('Failed to save settings');
    } finally {
      setSaving(false);
    }
  };

  const handleFieldChange = () => {
    setHasChanges(true);
  };

  const handleSignOut = async () => {
    try {
      await signOut();
      toast.success('Signed out successfully');
      navigate('/login');
    } catch (error) {
      toast.error('Failed to sign out');
    }
  };

  const toggleFocusSubject = (subject: string) => {
    setFocusSubjects(prev => {
      const newSubjects = prev.includes(subject)
        ? prev.filter(s => s !== subject)
        : [...prev, subject];
      handleFieldChange();
      return newSubjects;
    });
  };

  if (loading) {
    return (
      <MainLayout>
        <div className="flex items-center justify-center min-h-[60vh]">
          <div className="text-center space-y-4">
            <Loader2 className="h-8 w-8 animate-spin mx-auto text-primary" />
            <p className="text-muted-foreground">Loading settings...</p>
          </div>
        </div>
      </MainLayout>
    );
  }

  return (
    <MainLayout>
      <div className="p-4 sm:p-6 lg:p-8 max-w-3xl mx-auto space-y-4 sm:space-y-6 lg:space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-2xl sm:text-3xl font-bold text-foreground">Settings</h1>
          <p className="text-sm sm:text-base text-muted-foreground mt-1">
            Manage your account and preferences
          </p>
        </div>

        {/* Profile Section */}
        <Card>
          <CardHeader>
            <CardTitle>Profile</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-4 mb-6">
              <div className="w-16 h-16 rounded-full bg-primary flex items-center justify-center shrink-0">
                <User className="h-8 w-8 text-primary-foreground" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="font-semibold text-foreground text-sm sm:text-base">{name || 'Student'}</h3>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">{email}</p>
              </div>
            </div>

            <div className="space-y-4 sm:space-y-6">
              <div className="space-y-2">
                <Label htmlFor="name">Name</Label>
                <Input
                  id="name"
                  type="text"
                  value={name}
                  onChange={(e) => {
                    setName(e.target.value);
                    handleFieldChange();
                  }}
                  placeholder="Your display name"
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="email">Email</Label>
                <Input
                  id="email"
                  type="email"
                  value={email}
                  disabled
                  className="bg-muted"
                  placeholder="Your email"
                />
                <p className="text-xs text-muted-foreground">Email cannot be changed</p>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label htmlFor="phone">Phone Number (Optional)</Label>
                <Input
                  id="phone"
                  type="tel"
                  value={phone}
                  onChange={(e) => {
                    setPhone(e.target.value);
                    handleFieldChange();
                  }}
                  placeholder="Your phone number"
                />
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>Syllabus</Label>
                <Select
                  value={syllabus}
                  onValueChange={(value: 'cbse' | 'icse' | 'state') => {
                    setSyllabus(value);
                    handleFieldChange();
                  }}
                >
                  <SelectTrigger>
                    <SelectValue placeholder="Select your syllabus" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="cbse">CBSE</SelectItem>
                    <SelectItem value="icse">ICSE</SelectItem>
                    <SelectItem value="state">State Board</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <Separator />

              <div className="space-y-3">
                <Label>Your Class</Label>
                <GradeSelector
                  selectedGrade={grade}
                  onGradeSelect={(g) => {
                    setGrade(g);
                    handleFieldChange();
                  }}
                />
              </div>

              <Separator />

              <div className="space-y-3">
                <Label>Target Exam</Label>
                <TargetExamSelector
                  selectedExam={targetExam}
                  onExamSelect={(e) => {
                    setTargetExam(e);
                    handleFieldChange();
                  }}
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Preferences Section */}
        <Card>
          <CardHeader>
            <CardTitle>Preferences</CardTitle>
          </CardHeader>
          <CardContent className="p-0">
            <div className="divide-y divide-border">
              <div className="px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="p-2 rounded-lg bg-secondary shrink-0">
                    <Bell className="h-4 w-4 sm:h-5 sm:w-5 text-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-foreground text-sm sm:text-base">Push Notifications</p>
                    <p className="text-xs sm:text-sm text-muted-foreground">Get notified about tests and reminders</p>
                  </div>
                </div>
                <Switch
                  checked={notifications}
                  onCheckedChange={(checked) => {
                    setNotifications(checked);
                    handleFieldChange();
                  }}
                  className="shrink-0"
                />
              </div>

              <div className="px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="p-2 rounded-lg bg-secondary shrink-0">
                    <BookOpen className="h-4 w-4 sm:h-5 sm:w-5 text-foreground" />
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-foreground text-sm sm:text-base">Daily Study Reminders</p>
                    <p className="text-xs sm:text-sm text-muted-foreground">Remind me to study every day</p>
                  </div>
                </div>
                <Switch
                  checked={dailyReminders}
                  onCheckedChange={(checked) => {
                    setDailyReminders(checked);
                    handleFieldChange();
                  }}
                  className="shrink-0"
                />
              </div>

              <div className="px-4 sm:px-6 py-4 flex flex-col sm:flex-row sm:items-center sm:justify-between gap-3">
                <div className="flex items-center gap-3 flex-1 min-w-0">
                  <div className="p-2 rounded-lg bg-secondary shrink-0">
                    {darkMode ? <Moon className="h-4 w-4 sm:h-5 sm:w-5 text-foreground" /> : <Sun className="h-4 w-4 sm:h-5 sm:w-5 text-foreground" />}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-foreground text-sm sm:text-base">Dark Mode</p>
                    <p className="text-xs sm:text-sm text-muted-foreground">Use dark theme</p>
                  </div>
                </div>
                <Switch
                  checked={darkMode}
                  onCheckedChange={(checked) => {
                    setDarkMode(checked);
                    handleFieldChange();
                  }}
                  className="shrink-0"
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Study Preferences */}
        <Card>
          <CardHeader>
            <CardTitle>Study Preferences</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 sm:space-y-6">
            <div className="space-y-2">
              <Label>Difficulty Level</Label>
              <p className="text-xs sm:text-sm text-muted-foreground">Adjust question difficulty</p>
              <Select
                value={difficultyLevel}
                onValueChange={(value: "easy" | "adaptive" | "hard") => {
                  setDifficultyLevel(value);
                  handleFieldChange();
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="easy">Easy</SelectItem>
                  <SelectItem value="adaptive">Adaptive</SelectItem>
                  <SelectItem value="hard">Hard</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label>Daily Goal</Label>
              <p className="text-xs sm:text-sm text-muted-foreground">Questions per day</p>
              <div className="flex items-center gap-2">
                <Input
                  type="number"
                  min="1"
                  max="200"
                  value={dailyGoal}
                  onChange={(e) => {
                    setDailyGoal(e.target.value);
                    handleFieldChange();
                  }}
                  className="flex-1"
                />
                <span className="text-xs sm:text-sm text-muted-foreground whitespace-nowrap">questions</span>
              </div>
            </div>

            <div className="space-y-2">
              <Label>Focus Subjects</Label>
              <p className="text-xs sm:text-sm text-muted-foreground">Select subjects to prioritize</p>
              <div className="grid grid-cols-3 gap-3">
                {['physics', 'chemistry', 'mathematics'].map((subject) => (
                  <Button
                    key={subject}
                    type="button"
                    variant={focusSubjects.includes(subject) ? 'default' : 'outline'}
                    className="w-full capitalize"
                    onClick={() => toggleFocusSubject(subject)}
                  >
                    {subject}
                  </Button>
                ))}
              </div>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          {hasChanges && (
            <Button
              onClick={handleSaveSettings}
              disabled={saving}
              className="w-full sm:flex-1"
            >
              {saving ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Saving...
                </>
              ) : (
                <>
                  <Save className="h-4 w-4 mr-2" />
                  Save Settings
                </>
              )}
            </Button>
          )}
          <Button
            variant="outline"
            onClick={handleSignOut}
            className={cn("w-full sm:flex-1 text-destructive hover:text-destructive", !hasChanges && "sm:flex-1")}
          >
            <LogOut className="h-4 w-4 mr-2" />
            Sign Out
          </Button>
        </div>
      </div>
    </MainLayout>
  );
};

export default Settings;
