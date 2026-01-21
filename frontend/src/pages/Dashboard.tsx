import { MainLayout } from "@/components/layout/MainLayout";
import { StatsGrid } from "@/components/dashboard/StatsGrid";
import { SubjectCard } from "@/components/dashboard/SubjectCard";
import { PerformanceRadar } from "@/components/dashboard/PerformanceRadar";
import { RecentActivity } from "@/components/dashboard/RecentActivity";
import { StreakCard } from "@/components/dashboard/StreakCard";
import { UpcomingTestsWidget } from "@/components/dashboard/UpcomingTestsWidget";
import { RevisionCapsuleWidget } from "@/components/chat/RevisionCapsuleWidget";
import { Calculator, Atom, FlaskConical } from "lucide-react";

const subjectData = [
  {
    title: "Physics",
    icon: <Atom className="h-5 w-5" />,
    score: 78,
    change: 5,
    topics: [
      { name: "Mechanics", mastery: 85 },
      { name: "Thermodynamics", mastery: 72 },
      { name: "Electromagnetism", mastery: 68 },
    ],
  },
  {
    title: "Chemistry",
    icon: <FlaskConical className="h-5 w-5" />,
    score: 72,
    change: -2,
    topics: [
      { name: "Organic Chemistry", mastery: 80 },
      { name: "Inorganic Chemistry", mastery: 65 },
      { name: "Physical Chemistry", mastery: 70 },
    ],
  },
  {
    title: "Mathematics",
    icon: <Calculator className="h-5 w-5" />,
    score: 81,
    change: 8,
    topics: [
      { name: "Calculus", mastery: 90 },
      { name: "Algebra", mastery: 85 },
      { name: "Coordinate Geometry", mastery: 75 },
    ],
  },
];

const radarData = [
  { subject: "Mechanics", score: 85, fullMark: 100 },
  { subject: "Thermodynamics", score: 72, fullMark: 100 },
  { subject: "Electromagnetism", score: 68, fullMark: 100 },
  { subject: "Optics", score: 75, fullMark: 100 },
  { subject: "Modern Physics", score: 60, fullMark: 100 },
  { subject: "Waves", score: 82, fullMark: 100 },
];

const Dashboard = () => {
  return (
    <MainLayout>
      <div className="p-8 space-y-8">
        {/* Header */}
        <div>
          <h1 className="text-3xl font-bold text-foreground">Dashboard</h1>
          <p className="text-muted-foreground mt-1">
            Track your progress and identify areas for improvement
          </p>
        </div>

        {/* Stats */}
        <StatsGrid />

        {/* Main Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column - Charts and Analysis */}
          <div className="lg:col-span-2 space-y-6">
            {/* Subject Cards */}
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-4">Subject Performance</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                {subjectData.map((subject) => (
                  <SubjectCard key={subject.title} {...subject} />
                ))}
              </div>
            </div>

            {/* Performance Radar */}
            <PerformanceRadar data={radarData} title="Physics Topic Analysis" />

            {/* Recent Activity */}
            <div>
              <h2 className="text-xl font-semibold text-foreground mb-4">Recent Activity</h2>
              <RecentActivity />
            </div>
          </div>

          {/* Right Column - Sidebar Widgets */}
          <div className="space-y-6">
            {/* Upcoming Tests */}
            <UpcomingTestsWidget />

            {/* Streak Card */}
            <StreakCard />

            {/* Revision Capsule */}
            <RevisionCapsuleWidget subject="physics" />
          </div>
        </div>
      </div>
    </MainLayout>
  );
};

export default Dashboard;
