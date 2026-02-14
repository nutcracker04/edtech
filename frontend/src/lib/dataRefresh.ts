/**
 * Utility for managing data refresh across the application
 * Used to invalidate cached data when important events occur (e.g., test completion)
 */

const REFRESH_KEY = 'dashboard_refresh_timestamp';
const ANALYSIS_REFRESH_KEY = 'analysis_refresh_timestamp';

/**
 * Mark dashboard data as stale, triggering a refresh on next visit
 */
export function invalidateDashboardData() {
  localStorage.setItem(REFRESH_KEY, Date.now().toString());
}

/**
 * Mark analysis data as stale, triggering a refresh on next visit
 */
export function invalidateAnalysisData() {
  localStorage.setItem(ANALYSIS_REFRESH_KEY, Date.now().toString());
}

/**
 * Mark all data as stale
 */
export function invalidateAllData() {
  invalidateDashboardData();
  invalidateAnalysisData();
}

/**
 * Get the last refresh timestamp for dashboard
 */
export function getDashboardRefreshTimestamp(): number {
  const timestamp = localStorage.getItem(REFRESH_KEY);
  return timestamp ? parseInt(timestamp, 10) : 0;
}

/**
 * Get the last refresh timestamp for analysis
 */
export function getAnalysisRefreshTimestamp(): number {
  const timestamp = localStorage.getItem(ANALYSIS_REFRESH_KEY);
  return timestamp ? parseInt(timestamp, 10) : 0;
}

/**
 * Check if data should be refreshed based on timestamp
 * @param lastFetchTime - The timestamp when data was last fetched
 * @param refreshKey - The key to check for refresh timestamp
 */
export function shouldRefreshData(lastFetchTime: number, refreshKey: 'dashboard' | 'analysis'): boolean {
  const key = refreshKey === 'dashboard' ? REFRESH_KEY : ANALYSIS_REFRESH_KEY;
  const refreshTimestamp = localStorage.getItem(key);
  
  if (!refreshTimestamp) return false;
  
  const refreshTime = parseInt(refreshTimestamp, 10);
  return refreshTime > lastFetchTime;
}
