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
  AlertCircle,
  Sparkles,
  GraduationCap,
} from "lucide-react";
import { Button } from "@/components/ui/button";

const navItems = [
  { icon: MessageSquare, label: "Home", href: "/", highlight: false },
  { icon: LayoutDashboard, label: "Dashboard", href: "/dashboard" },
  { icon: BookOpen, label: "My Tests", href: "/tests" },
  { icon: Upload, label: "Upload Test", href: "/upload-test", highlight: false },
  { icon: Target, label: "Analysis", href: "/analysis" },
  { icon: AlertCircle, label: "Mistakes", href: "/mistakes" },
  { icon: Sparkles, label: "Revision", href: "/revision-capsules" },
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
      onMouseEnter={() => !mobile && onCollapse(false)}
      onMouseLeave={() => !mobile && onCollapse(true)}
      className={cn(
        "h-screen bg-sidebar border-r border-sidebar-border transition-all duration-300 flex flex-col",
        mobile ? "w-full" : "fixed left-0 top-0 z-40",
        !mobile && (collapsed ? "w-16" : "w-56")
      )}
    >
      {/* Logo */}
      <div className="flex items-center justify-center h-16 border-b border-sidebar-border relative">
        {(!collapsed || mobile) ? (
          <button
            onClick={handleLogoClick}
            className="font-bold text-xl text-sidebar-foreground tracking-tight hover:opacity-80 transition-opacity w-full text-center"
            aria-label="Go to home"
          >
            Catalyst
          </button>
        ) : (
          <button
            onClick={handleLogoClick}
            className="font-bold text-xl text-sidebar-foreground tracking-tight hover:opacity-80 transition-opacity w-full text-center"
            aria-label="Go to home"
          >
            C
          </button>
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
              <span className={cn(
                "text-xs sm:text-sm font-medium truncate transition-all duration-300 origin-left",
                (collapsed && !mobile) ? "opacity-0 w-0 scale-x-0" : "opacity-100 w-auto scale-x-100 ml-0"
              )}>
                {item.label}
              </span>
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
              <span className={cn(
                "text-xs sm:text-sm font-medium truncate transition-all duration-300 origin-left",
                (collapsed && !mobile) ? "opacity-0 w-0 scale-x-0" : "opacity-100 w-auto scale-x-100 ml-0"
              )}>
                {item.label}
              </span>
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
              <span className={cn(
                "text-xs sm:text-sm font-medium truncate transition-all duration-300 origin-left",
                (collapsed && !mobile) ? "opacity-0 w-0 scale-x-0" : "opacity-100 w-auto scale-x-100 ml-0"
              )}>
                {item.label}
              </span>
            </Link>
          );
        })}
      </div>
    </aside>
  );
}
