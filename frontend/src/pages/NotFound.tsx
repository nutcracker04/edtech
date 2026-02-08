import { useLocation, useNavigate } from "react-router-dom";
import { useEffect } from "react";
import { Button } from "@/components/ui/button";
import { Home, ArrowLeft, AlertTriangle } from "lucide-react";

const NotFound = () => {
  const location = useLocation();
  const navigate = useNavigate();

  useEffect(() => {
    console.error("404 Error: User attempted to access non-existent route:", location.pathname);
  }, [location.pathname]);

  return (
    <div className="flex min-h-screen items-center justify-center bg-gradient-to-br from-background via-background to-secondary/50">
      <div className="text-center space-y-8 max-w-md mx-auto px-6">
        {/* Icon */}
        <div className="flex justify-center">
          <div className="w-24 h-24 rounded-full bg-primary/10 border border-primary/20 flex items-center justify-center">
            <AlertTriangle className="h-12 w-12 text-primary" />
          </div>
        </div>

        {/* Content */}
        <div className="space-y-3">
          <h1 className="text-6xl font-bold text-foreground">404</h1>
          <h2 className="text-2xl font-semibold text-foreground">Page Not Found</h2>
          <p className="text-muted-foreground">
            The page you're looking for doesn't exist or has been moved.
          </p>
          {location.pathname !== "/" && (
            <p className="text-xs text-muted-foreground bg-secondary/50 rounded-lg p-3">
              Attempted path: <code className="text-primary">{location.pathname}</code>
            </p>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex flex-col gap-3 pt-4">
          <Button
            onClick={() => navigate(-1)}
            variant="outline"
            className="w-full gap-2"
          >
            <ArrowLeft className="h-4 w-4" />
            Go Back
          </Button>
          <Button
            onClick={() => navigate("/")}
            className="w-full gap-2"
          >
            <Home className="h-4 w-4" />
            Return Home
          </Button>
        </div>

        {/* Links */}
        <div className="grid grid-cols-3 gap-2 pt-6 border-t border-border">
          <button
            onClick={() => navigate("/dashboard")}
            className="p-3 rounded-lg hover:bg-secondary/50 transition-colors text-sm text-muted-foreground hover:text-foreground"
          >
            Dashboard
          </button>
          <button
            onClick={() => navigate("/analysis")}
            className="p-3 rounded-lg hover:bg-secondary/50 transition-colors text-sm text-muted-foreground hover:text-foreground"
          >
            Analysis
          </button>
          <button
            onClick={() => navigate("/tests")}
            className="p-3 rounded-lg hover:bg-secondary/50 transition-colors text-sm text-muted-foreground hover:text-foreground"
          >
            Tests
          </button>
        </div>
      </div>
    </div>
  );
};

export default NotFound;
