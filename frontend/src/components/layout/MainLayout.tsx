import { ReactNode, useEffect, useState } from "react";
import { Sidebar } from "./Sidebar";
import { cn } from "@/lib/utils";
import { useIsMobile } from "@/hooks/use-mobile";
import { Sheet, SheetContent, SheetTrigger } from "@/components/ui/sheet";
import { Button } from "@/components/ui/button";
import { Menu } from "lucide-react";

interface MainLayoutProps {
  children: ReactNode;
}

export function MainLayout({ children }: MainLayoutProps) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const isMobile = useIsMobile();

  useEffect(() => {
    // Ensure light mode is enabled by default
    document.documentElement.classList.remove("dark");
  }, []);

  return (
    <div className="min-h-screen bg-background">
      {/* Desktop Sidebar */}
      {!isMobile && (
        <Sidebar collapsed={sidebarCollapsed} onCollapse={setSidebarCollapsed} />
      )}

      {/* Mobile Sidebar */}
      {isMobile && (
        <Sheet open={mobileMenuOpen} onOpenChange={setMobileMenuOpen}>
          <SheetTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="fixed top-3 left-3 sm:top-4 sm:left-4 z-50 md:hidden h-9 w-9 sm:h-10 sm:w-10"
              aria-label="Open menu"
            >
              <Menu className="h-5 w-5 sm:h-6 sm:w-6" />
            </Button>
          </SheetTrigger>
          <SheetContent side="left" className="w-[85vw] max-w-sm p-0">
            <Sidebar
              collapsed={false}
              onCollapse={() => { }}
              mobile={true}
              onMobileClose={() => setMobileMenuOpen(false)}
            />
          </SheetContent>
        </Sheet>
      )}

      <main className={cn(
        "transition-all duration-300",
        isMobile ? "ml-0" : sidebarCollapsed ? "ml-16" : "ml-56"
      )}>
        {children}
      </main>
    </div>
  );
}
