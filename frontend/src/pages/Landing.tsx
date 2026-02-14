import { useEffect } from "react";
import { Link } from "react-router-dom";
import { Button } from "@/components/ui/button";
import { BookOpen, Target, Zap } from "lucide-react";

export default function Landing() {
  useEffect(() => {
    document.documentElement.classList.remove("dark");
  }, []);

  return (
    <div className="min-h-screen bg-background flex flex-col">
      {/* Top bar - minimal */}
      <header className="flex items-center justify-between p-4 sm:p-6">
        <span className="font-bold text-xl text-foreground tracking-tight">
          Catalyst
        </span>
        <Link to="/login">
          <Button variant="ghost" size="sm" className="text-foreground font-medium">
            Sign in
          </Button>
        </Link>
      </header>

      {/* Main content - one idea, big and clear */}
      <main className="flex-1 flex flex-col items-center justify-center px-4 sm:px-6 py-8 text-center max-w-2xl mx-auto">
        <h1 className="text-4xl sm:text-5xl font-extrabold text-foreground tracking-tight leading-tight font-[family-name:var(--font-display)]">
          Practice tests.
          <br />
          <span className="text-primary">See where you stand.</span>
        </h1>
        <p className="mt-5 text-lg sm:text-xl text-muted-foreground font-medium max-w-md">
          Take tests, find your weak spots, and get better. Simple.
        </p>

        {/* Three short benefits - icons + one word each */}
        <ul className="mt-10 flex flex-wrap justify-center gap-6 sm:gap-10 text-muted-foreground">
          <li className="flex items-center gap-2">
            <BookOpen className="h-5 w-5 text-primary" aria-hidden />
            <span className="font-medium">Take tests</span>
          </li>
          <li className="flex items-center gap-2">
            <Target className="h-5 w-5 text-primary" aria-hidden />
            <span className="font-medium">See weak spots</span>
          </li>
          <li className="flex items-center gap-2">
            <Zap className="h-5 w-5 text-primary" aria-hidden />
            <span className="font-medium">Improve</span>
          </li>
        </ul>

        {/* Two clear actions */}
        <div className="mt-12 flex flex-col sm:flex-row gap-3 w-full sm:w-auto sm:min-w-[280px]">
          <Link to="/onboarding" className="flex-1 sm:flex-initial">
            <Button size="lg" className="w-full h-12 text-base font-semibold">
              Get started — it’s free
            </Button>
          </Link>
          <Link to="/login" className="flex-1 sm:flex-initial">
            <Button variant="outline" size="lg" className="w-full h-12 text-base font-semibold">
              I already have an account
            </Button>
          </Link>
        </div>
      </main>

      {/* Optional footer - one line */}
      <footer className="p-4 text-center text-sm text-muted-foreground">
        For students preparing for exams.
      </footer>
    </div>
  );
}
