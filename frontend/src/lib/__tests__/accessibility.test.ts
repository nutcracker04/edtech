import { describe, it, expect } from 'vitest';
import {
  generatePerformanceAriaLabel,
  generateStreakAriaLabel,
  generateTrendAriaLabel,
  generateVisualizationAriaLabel,
  generateActionAriaLabel,
  getFocusVisibleStyle,
} from '../accessibility';

describe('accessibility utilities', () => {
  describe('generatePerformanceAriaLabel', () => {
    it('generates correct ARIA label for strong performance', () => {
      const label = generatePerformanceAriaLabel('Mathematics', 85, 100);
      expect(label).toContain('Mathematics');
      expect(label).toContain('85%');
      expect(label).toContain('strong');
      expect(label).toContain('100 questions');
    });

    it('generates correct ARIA label for average performance', () => {
      const label = generatePerformanceAriaLabel('Physics', 65, 50);
      expect(label).toContain('Physics');
      expect(label).toContain('65%');
      expect(label).toContain('average');
      expect(label).toContain('50 questions');
    });

    it('generates correct ARIA label for weak performance', () => {
      const label = generatePerformanceAriaLabel('Chemistry', 45, 30);
      expect(label).toContain('Chemistry');
      expect(label).toContain('45%');
      expect(label).toContain('weak');
      expect(label).toContain('30 questions');
    });
  });

  describe('generateStreakAriaLabel', () => {
    it('generates label for regular streak', () => {
      const label = generateStreakAriaLabel(5, false);
      expect(label).toContain('5 consecutive days');
      expect(label).not.toContain('milestone');
    });

    it('generates label for milestone streak', () => {
      const label = generateStreakAriaLabel(7, true, 7);
      expect(label).toContain('7 consecutive days');
      expect(label).toContain('milestone reached: 7 days');
    });
  });

  describe('generateTrendAriaLabel', () => {
    it('generates correct labels for different trends', () => {
      expect(generateTrendAriaLabel('up')).toBe('Performance improving');
      expect(generateTrendAriaLabel('down')).toBe('Performance declining');
      expect(generateTrendAriaLabel('flat')).toBe('Performance stable');
    });
  });

  describe('generateVisualizationAriaLabel', () => {
    it('generates correct label for visualization', () => {
      const label = generateVisualizationAriaLabel('Progress Rings', 5);
      expect(label).toContain('Progress Rings');
      expect(label).toContain('5 subjects');
    });
  });

  describe('generateActionAriaLabel', () => {
    it('generates correct label for actions', () => {
      const label = generateActionAriaLabel('Practice', 'Algebra');
      expect(label).toBe('Practice for Algebra');
    });
  });

  describe('getFocusVisibleStyle', () => {
    it('returns focus visible style classes', () => {
      const style = getFocusVisibleStyle();
      expect(style).toContain('focus:outline-none');
      expect(style).toContain('focus:ring-2');
      expect(style).toContain('focus:ring-blue-500');
    });
  });
});
