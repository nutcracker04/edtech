import * as React from "react";

interface LazyItemProps {
  children: React.ReactNode;
  fallback?: React.ReactNode;
  className?: string;
}

/**
 * LazyItem - A component that lazy-loads its content when it comes into view
 * 
 * Use this component inside a ScrollableContainer with enableLazyLoading={true}
 * to defer rendering of off-screen content until it's needed.
 * 
 * @example
 * ```tsx
 * <ScrollableContainer enableLazyLoading={true}>
 *   {items.map(item => (
 *     <LazyItem key={item.id} fallback={<Skeleton />}>
 *       <ExpensiveComponent item={item} />
 *     </LazyItem>
 *   ))}
 * </ScrollableContainer>
 * ```
 */
export const LazyItem: React.FC<LazyItemProps> = ({ 
  children, 
  fallback = null,
  className 
}) => {
  const [isLoaded, setIsLoaded] = React.useState(false);
  const ref = React.useRef<HTMLDivElement>(null);

  React.useEffect(() => {
    const element = ref.current;
    if (!element) return;

    // Check if already loaded via data attribute (set by ScrollableContainer)
    const checkLoaded = () => {
      if (element.hasAttribute("data-lazy-loaded")) {
        setIsLoaded(true);
      }
    };

    checkLoaded();

    // Watch for attribute changes
    const observer = new MutationObserver(checkLoaded);
    observer.observe(element, { attributes: true, attributeFilter: ["data-lazy-loaded"] });

    return () => observer.disconnect();
  }, []);

  return (
    <div ref={ref} data-lazy="true" className={className}>
      {isLoaded ? children : fallback}
    </div>
  );
};
