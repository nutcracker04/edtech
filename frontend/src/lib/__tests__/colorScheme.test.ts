import { describe, it, expect } from 'vitest';
import {
  getPerformanceColor,
  getPerformanceLabel,
  getPerformanceColorClass,
  PERFORMANCE_COLORS,
} from '../colorScheme';

describe('colorScheme utilities', () => {
  describe('getPerformanceColor', () => {
    it('returns strong color for accuracy >= 80', () => {
      expect(getPerformanceColor(80)).toBe(PERFORMANCE_COLORS.strong);
      expect(getPerformanceColor(90)).toBe(PERFORMANCE_COLORS.strong);
      expect(getPerformanceColor(100)).toBe(PERFORMANCE_COLORS.strong);
    });

    it('returns average color for accuracy 60-79', () => {
      expect(getPerformanceColor(60)).toBe(PERFORMANCE_COLORS.average);
      expect(getPerformanceColor(70)).toBe(PERFORMANCE_COLORS.average);
      expect(getPerformanceColor(79)).toBe(PERFORMANCE_COLORS.average);
    });

    it('returns weak color for accuracy < 60', () => {
      expect(getPerformanceColor(0)).toBe(PERFORMANCE_COLORS.weak);
      expect(getPerformanceColor(30)).toBe(PERFORMANCE_COLORS.weak);
      expect(getPerformanceColor(59)).toBe(PERFORMANCE_COLORS.weak);
    });
  });

  describe('getPerformanceLabel', () => {
    it('returns correct labels for different accuracy levels', () => {
      expect(getPerformanceLabel(85)).toBe('Strong');
      expect(getPerformanceLabel(65)).toBe('Average');
      expect(getPerformanceLabel(45)).toBe('Weak');
    });
  });

  describe('getPerformanceColorClass', () => {
    it('returns correct Tailwind classes for different accuracy levels', () => {
      expect(getPerformanceColorClass(85)).toBe('text-green-600');
      expect(getPerformanceColorClass(65)).toBe('text-yellow-600');
      expect(getPerformanceColorClass(45)).toBe('text-red-600');
    });
  });

  describe('color consistency', () => {
    it('uses consistent color values across all color constants', () => {
      // Verify that the same color values are used across different formats
      expect(PERFORMANCE_COLORS.strong).toBe('#10b981');
      expect(PERFORMANCE_COLORS.average).toBe('#f59e0b');
      expect(PERFORMANCE_COLORS.weak).toBe('#ef4444');
    });
  });
});
