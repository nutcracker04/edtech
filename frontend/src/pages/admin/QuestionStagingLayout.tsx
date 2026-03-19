/**
 * Shared shell for question import + batch review (single admin flow).
 */

import { NavLink, Outlet, useNavigate } from 'react-router-dom';
import { MainLayout } from '@/components/layout/MainLayout';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';
import { ArrowLeft, Layers, Upload } from 'lucide-react';

const linkClass =
  'inline-flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors';
const activeClass = 'bg-primary text-primary-foreground';
const idleClass = 'text-muted-foreground hover:bg-muted hover:text-foreground';

export function QuestionStagingLayout() {
  const navigate = useNavigate();

  return (
    <MainLayout>
      <div className="border-b bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80">
        <div className="container flex flex-wrap items-center gap-3 py-4">
          <Button variant="ghost" size="sm" className="gap-2 shrink-0" onClick={() => navigate('/admin')}>
            <ArrowLeft className="h-4 w-4" />
            Admin home
          </Button>
          <div className="h-6 w-px bg-border hidden sm:block" />
          <h1 className="text-lg font-semibold tracking-tight">Questions</h1>
          <nav className="flex flex-wrap items-center gap-1 sm:ml-2">
            <NavLink
              to="/admin/questions/import"
              className={({ isActive }) => cn(linkClass, isActive ? activeClass : idleClass)}
            >
              <Upload className="h-4 w-4" />
              Import batch
            </NavLink>
            <NavLink
              to="/admin/questions"
              end
              className={({ isActive }) => cn(linkClass, isActive ? activeClass : idleClass)}
            >
              <Layers className="h-4 w-4" />
              All batches
            </NavLink>
          </nav>
        </div>
      </div>
      <Outlet />
    </MainLayout>
  );
}
