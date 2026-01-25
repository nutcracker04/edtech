import { Link, useLocation, useNavigate } from "react-router-dom";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/lib/utils";
import {
  Plus,
  LayoutDashboard,
  BookOpen,
  Target,
  Settings,
  ChevronLeft,
  ChevronRight,
  MessageSquare,
  Upload,
  Shield,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Logo } from "@/components/ui/Logo";

const navItems = [
  { icon: MessageSquare, label: "Home", href: "/", highlight: false },
  { icon: Plus, label: "New Practice", href: "/practice", highlight: true },
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: BookOpen, label: "My Tests", href: "/tests" },
  { icon: Upload, label: "Upload Test", href: "/upload-test", highlight: false },
  { icon: Target, label: "Analysis", href: "/analysis" },
];

const adminItems = [
  { icon: Shield, label: "Admin Panel", href: "/admin", highlight: false },
];

const bottomItems = [
  { icon: Settings, label: "Settings", href: "/settings" },
];

interface SidebarProps {
  collapsed: boolean;
  onCollapse: (collapsed: boolean) => void;
  mobile?: boolean;
  onMobileClose?: () => void;
}

export function Sidebar({ collapsed, onCollapse, mobile = false, onMobileClose }: SidebarProps) {
  const { profile } = useAuth();
  const location = useLocation();
  const navigate = useNavigate();

  const handleLogoClick = () => {
    navigate("/");
    if (mobile && onMobileClose) {
      onMobileClose();
    }
  };

  const handleLinkClick = () => {
    if (mobile && onMobileClose) {
      onMobileClose();
    }
  };

  return (
    <aside
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300 flex flex-col",
        mobile ? "w-full" : "fixed left-0 top-0 z-40",
        !mobile && (collapsed ? "w-16" : "w-56")
      )}
    >
      {/* Logo */}
      <div className="flex items-center gap-2 sm:gap-3 p-3 sm:p-4 border-b border-sidebar-border">
        <button
          onClick={handleLogoClick}
          className="shrink-0 hover:opacity-80 transition-opacity flex items-center justify-center"
          aria-label="Go to home"
        >
          <Logo size="md" />
        </button>
        {(!collapsed || mobile) && (
          <button
            onClick={handleLogoClick}
            className="font-semibold text-sidebar-foreground hover:text-primary transition-colors text-sm sm:text-base truncate flex-1 min-w-0"
            aria-label="Go to home"
          >
            Catalyst
          </button>
        )}
        {!mobile && (
          <Button
            variant="ghost"
            size="icon"
            className={cn(
              "ml-auto h-6 w-6 text-muted-foreground hover:text-foreground",
              collapsed && "mx-auto ml-0"
            )}
            onClick={() => onCollapse(!collapsed)}
          >
            {collapsed ? <ChevronRight className="h-4 w-4" /> : <ChevronLeft className="h-4 w-4" />}
          </Button>
        )}
      </div>

      {/* Navigation */}
      <nav className="flex-1 p-2 sm:p-3 space-y-1 overflow-y-auto">
        {navItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              onClick={handleLinkClick}
              className={cn(
                "flex items-center gap-2 sm:gap-3 px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 min-w-0",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50",
                item.highlight && !isActive && "text-primary hover:text-primary"
              )}
            >
              <item.icon className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" />
              {(!collapsed || mobile) && (
                <span className="text-xs sm:text-sm font-medium truncate">{item.label}</span>
              )}
            </Link>
          );
        })}

        {profile?.role === 'admin' && adminItems.map((item) => {
          const isActive = location.pathname.startsWith(item.href);
          return (
            <Link
              key={item.href}
              to={item.href}
              onClick={handleLinkClick}
              className={cn(
                "flex items-center gap-2 sm:gap-3 px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 min-w-0 border border-primary/20 bg-primary/5 mt-4",
                isActive
                  ? "bg-primary text-primary-foreground"
                  : "text-primary hover:bg-primary/10"
              )}
            >
              <item.icon className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" />
              {(!collapsed || mobile) && (
                <span className="text-xs sm:text-sm font-medium truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </nav>

      {/* Bottom Section */}
      <div className="p-2 sm:p-3 space-y-1 border-t border-sidebar-border">
        {bottomItems.map((item) => {
          const isActive = location.pathname === item.href;
          return (
            <Link
              key={item.href}
              to={item.href}
              onClick={handleLinkClick}
              className={cn(
                "flex items-center gap-2 sm:gap-3 px-2 sm:px-3 py-2 sm:py-2.5 rounded-lg transition-all duration-200 min-w-0",
                isActive
                  ? "bg-sidebar-accent text-sidebar-accent-foreground"
                  : "text-muted-foreground hover:text-sidebar-foreground hover:bg-sidebar-accent/50"
              )}
            >
              <item.icon className="h-4 w-4 sm:h-5 sm:w-5 shrink-0" />
              {(!collapsed || mobile) && (
                <span className="text-xs sm:text-sm font-medium truncate">{item.label}</span>
              )}
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
