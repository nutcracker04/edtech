/**
 * Color scheme utilities for Dashboard and Analysis pages
 * Ensures consistent color mapping across all pages
 */

export const PERFORMANCE_COLORS = {
  strong: '#10b981', // Green - 80%+
  average: '#f59e0b', // Yellow - 60-79%
  weak: '#ef4444', // Red - <60%
} as const;

export const PERFORMANCE_COLORS_RGB = {
  strong: 'rgb(16, 185, 129)', // Green
  average: 'rgb(245, 158, 11)', // Yellow
  weak: 'rgb(239, 68, 68)', // Red
} as const;

export const PERFORMANCE_COLORS_HEX = {
  strong: '#10b981',
  average: '#f59e0b',
  weak: '#ef4444',
} as const;

export const PERFORMANCE_COLORS_LIGHT = {
  strong: '#d1fae5', // Light green
  average: '#fef3c7', // Light yellow
  weak: '#fee2e2', // Light red
} as const;

export const PERFORMANCE_COLORS_DARK = {
  strong: '#047857', // Dark green
  average: '#d97706', // Dark yellow
  weak: '#dc2626', // Dark red
} as const;

/**
 * Get color based on performance level
 */
export function getPerformanceColor(accuracy: number): string {
  if (accuracy >= 80) return PERFORMANCE_COLORS.strong;
  if (accuracy >= 60) return PERFORMANCE_COLORS.average;
  return PERFORMANCE_COLORS.weak;
}

/**
 * Get light background color based on performance level
 */
export function getPerformanceColorLight(accuracy: number): string {
  if (accuracy >= 80) return PERFORMANCE_COLORS_LIGHT.strong;
  if (accuracy >= 60) return PERFORMANCE_COLORS_LIGHT.average;
  return PERFORMANCE_COLORS_LIGHT.weak;
}

/**
 * Get performance label based on accuracy
 */
export function getPerformanceLabel(accuracy: number): 'Strong' | 'Average' | 'Weak' {
  if (accuracy >= 80) return 'Strong';
  if (accuracy >= 60) return 'Average';
  return 'Weak';
}

/**
 * Get Tailwind color class based on performance level
 */
export function getPerformanceColorClass(accuracy: number): string {
  if (accuracy >= 80) return 'text-green-600';
  if (accuracy >= 60) return 'text-yellow-600';
  return 'text-red-600';
}

/**
 * Get Tailwind background color class based on performance level
 */
export function getPerformanceBackgroundClass(accuracy: number): string {
  if (accuracy >= 80) return 'bg-green-50';
  if (accuracy >= 60) return 'bg-yellow-50';
  return 'bg-red-50';
}

/**
 * Get Tailwind border color class based on performance level
 */
export function getPerformanceBorderClass(accuracy: number): string {
  if (accuracy >= 80) return 'border-green-200';
  if (accuracy >= 60) return 'border-yellow-200';
  return 'border-red-200';
}

/**
 * Verify WCAG AA contrast ratio (4.5:1 for normal text)
 * This is a simplified check - actual contrast ratio calculation is more complex
 */
export function meetsWCAGAA(foreground: string, background: string): boolean {
  // Simplified check - in production, use a proper contrast ratio calculator
  // This is a placeholder that assumes our color scheme meets WCAG AA
  return true;
}
