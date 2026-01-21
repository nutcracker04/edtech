import { useState } from "react";
import { MainLayout } from "@/components/layout/MainLayout";
import { User, Bell, BookOpen, Moon, Sun, ChevronRight, LogOut, Save } from "lucide-react";
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

const Settings = () => {
  const [name, setName] = useState("Student");
  const [email, setEmail] = useState("student@example.com");
  const [grade, setGrade] = useState<Grade | null>("12");
  const [targetExam, setTargetExam] = useState<TargetExam | null>("jee-main");
  const [notifications, setNotifications] = useState(true);
  const [dailyReminders, setDailyReminders] = useState(true);
  const [darkMode, setDarkMode] = useState(true);
  const [dailyGoal, setDailyGoal] = useState("50");
  const [difficultyLevel, setDifficultyLevel] = useState("adaptive");
  const [focusSubjects, setFocusSubjects] = useState("all");
  const [hasChanges, setHasChanges] = useState(false);

  const handleSaveSettings = () => {
    // Save settings to localStorage
    const settings = {
      name,
      email,
      grade,
      targetExam,
      notifications,
      dailyReminders,
      darkMode,
      dailyGoal: parseInt(dailyGoal),
      difficultyLevel,
      focusSubjects,
    };
    localStorage.setItem("jee-settings", JSON.stringify(settings));
    setHasChanges(false);
  };

  const handleFieldChange = () => {
    setHasChanges(true);
  };

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
                <h3 className="font-semibold text-foreground text-sm sm:text-base">Student</h3>
                <p className="text-xs sm:text-sm text-muted-foreground truncate">student@example.com</p>
              </div>
              <Button variant="outline" size="sm" className="w-full sm:w-auto">
                Edit Profile
              </Button>
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
                  onChange={(e) => {
                    setEmail(e.target.value);
                    handleFieldChange();
                  }}
                  placeholder="Your email"
                />
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
                <Switch checked={notifications} onCheckedChange={setNotifications} className="shrink-0" />
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
                <Switch checked={dailyReminders} onCheckedChange={setDailyReminders} className="shrink-0" />
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
                <Switch checked={darkMode} onCheckedChange={setDarkMode} className="shrink-0" />
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
                onValueChange={(value) => {
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
              <p className="text-xs sm:text-sm text-muted-foreground">Prioritize certain subjects</p>
              <Select
                value={focusSubjects}
                onValueChange={(value) => {
                  setFocusSubjects(value);
                  handleFieldChange();
                }}
              >
                <SelectTrigger>
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All subjects</SelectItem>
                  <SelectItem value="physics">Physics Only</SelectItem>
                  <SelectItem value="chemistry">Chemistry Only</SelectItem>
                  <SelectItem value="mathematics">Mathematics Only</SelectItem>
                  <SelectItem value="physics-chemistry">Physics & Chemistry</SelectItem>
                  <SelectItem value="physics-mathematics">Physics & Mathematics</SelectItem>
                  <SelectItem value="chemistry-mathematics">Chemistry & Mathematics</SelectItem>
                </SelectContent>
              </Select>
            </div>
          </CardContent>
        </Card>

        {/* Action Buttons */}
        <div className="flex flex-col sm:flex-row gap-3">
          {hasChanges && (
            <Button 
              onClick={handleSaveSettings}
              className="w-full sm:flex-1"
            >
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </Button>
          )}
          <Button 
            variant="outline" 
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
