import { ChevronRight, Home } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { cn } from '@/lib/utils';

interface BreadcrumbItem {
  label: string;
  onClick: () => void;
}

interface PerformanceBreadcrumbProps {
  items: BreadcrumbItem[];
}

export function PerformanceBreadcrumb({ items }: PerformanceBreadcrumbProps) {
  return (
    <nav className="flex items-center space-x-1 text-sm">
      <Button
        variant="ghost"
        size="sm"
        onClick={items[0]?.onClick}
        className="h-8 px-2"
      >
        <Home className="h-4 w-4" />
      </Button>
      {items.map((item, index) => (
        <div key={index} className="flex items-center">
          <ChevronRight className="h-4 w-4 text-muted-foreground" />
          <Button
            variant="ghost"
            size="sm"
            onClick={item.onClick}
            className={cn(
              'h-8 px-2',
              index === items.length - 1
                ? 'text-foreground font-medium'
                : 'text-muted-foreground hover:text-foreground'
            )}
          >
            {item.label}
          </Button>
        </div>
      ))}
    </nav>
  );
}
