/**
 * Accessibility utilities for Dashboard and Analysis pages
 * Ensures WCAG AA compliance
 */

/**
 * Generate ARIA label for performance metrics
 */
export function generatePerformanceAriaLabel(
  subject: string,
  accuracy: number,
  questions: number
): string {
  const level = accuracy >= 80 ? 'strong' : accuracy >= 60 ? 'average' : 'weak';
  return `${subject}: ${accuracy}% accuracy, ${level} performance, ${questions} questions solved`;
}

/**
 * Generate ARIA label for streak card
 */
export function generateStreakAriaLabel(
  currentStreak: number,
  isMilestone: boolean,
  milestoneValue?: number
): string {
  let label = `Current streak: ${currentStreak} consecutive days`;
  if (isMilestone && milestoneValue) {
    label += `, milestone reached: ${milestoneValue} days`;
  }
  return label;
}

/**
 * Generate ARIA label for trend indicator
 */
export function generateTrendAriaLabel(trend: 'up' | 'down' | 'flat'): string {
  switch (trend) {
    case 'up':
      return 'Performance improving';
    case 'down':
      return 'Performance declining';
    case 'flat':
      return 'Performance stable';
    default:
      return 'Performance trend unknown';
  }
}

/**
 * Generate ARIA label for visualization
 */
export function generateVisualizationAriaLabel(
  type: string,
  subjects: number
): string {
  return `${type} visualization showing performance for ${subjects} subjects`;
}

/**
 * Generate ARIA label for button action
 */
export function generateActionAriaLabel(action: string, context: string): string {
  return `${action} for ${context}`;
}

/**
 * Check if element is keyboard accessible
 */
export function isKeyboardAccessible(element: HTMLElement): boolean {
  const tabindex = element.getAttribute('tabindex');
  const isButton = element.tagName === 'BUTTON';
  const isLink = element.tagName === 'A';
  const isInput = element.tagName === 'INPUT' || element.tagName === 'TEXTAREA';

  return (
    isButton ||
    isLink ||
    isInput ||
    (tabindex !== null && parseInt(tabindex) >= 0)
  );
}

/**
 * Get focus visible style
 */
export function getFocusVisibleStyle(): string {
  return 'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2';
}

/**
 * Generate alt text for chart
 */
export function generateChartAltText(
  chartType: string,
  title: string,
  description: string
): string {
  return `${chartType}: ${title}. ${description}`;
}

/**
 * Ensure minimum touch target size (44px)
 */
export function ensureMinimumTouchSize(element: HTMLElement): boolean {
  const rect = element.getBoundingClientRect();
  return rect.width >= 44 && rect.height >= 44;
}

/**
 * Generate skip link for keyboard navigation
 */
export function generateSkipLink(targetId: string, label: string = 'Skip to main content'): string {
  return `<a href="#${targetId}" class="sr-only focus:not-sr-only">${label}</a>`;
}
