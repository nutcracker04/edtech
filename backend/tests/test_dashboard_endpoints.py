"""
Tests for Dashboard API endpoints
Validates that all required endpoints are implemented correctly
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from app.main import app
from app.utils.auth import get_current_user
from app.models.dashboard import (
    DashboardMetrics,
    StreakData,
    SubjectPerformance,
    ActivityItem,
    DashboardData,
)


# Mock user for authentication
def mock_get_current_user():
    return {"user_id": "test_user_123"}


# Mock authentication and supabase for all tests
@pytest.fixture(autouse=True)
def mock_dependencies():
    # Override the authentication dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("app.routers.dashboard.supabase") as mock_supabase:
        yield {"supabase": mock_supabase}
    
    # Clean up
    app.dependency_overrides.clear()


client = TestClient(app)


def test_get_dashboard_metrics_endpoint_exists(mock_dependencies):
    """Test that the /api/dashboard/metrics endpoint exists and returns correct structure"""
    # Mock data
    mock_supabase = mock_dependencies["supabase"]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    response = client.get("/api/dashboard/metrics")
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should have correct structure
    data = response.json()
    assert "accuracy_percentage" in data
    assert "questions_solved" in data
    assert "study_hours" in data
    assert "tests_completed" in data


def test_get_dashboard_metrics_calculates_correctly(mock_dependencies):
    """Test that metrics are calculated correctly from database data"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topic mastery data
    mastery_data = [
        {"questions_attempted": 10, "questions_correct": 8},
        {"questions_attempted": 20, "questions_correct": 16},
    ]
    
    # Mock tests data
    tests_data = [
        {"status": "completed"},
        {"status": "completed"},
        {"status": "in_progress"},
    ]
    
    # Mock activity data
    activity_data = [
        {"time_spent": 3600},  # 1 hour
        {"time_spent": 7200},  # 2 hours
    ]
    
    # Setup mock to return different data for different tables
    def mock_table_select(table_name):
        mock_chain = Mock()
        if table_name == "topic_mastery":
            mock_chain.select.return_value.eq.return_value.execute.return_value.data = mastery_data
        elif table_name == "tests":
            mock_chain.select.return_value.eq.return_value.execute.return_value.data = tests_data
        elif table_name == "user_activity":
            mock_chain.select.return_value.eq.return_value.execute.return_value.data = activity_data
        return mock_chain
    
    mock_supabase.table.side_effect = lambda name: mock_table_select(name)
    
    response = client.get("/api/dashboard/metrics")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify calculations
    # Total questions: 10 + 20 = 30
    # Total correct: 8 + 16 = 24
    # Accuracy: 24/30 * 100 = 80%
    assert data["questions_solved"] == 30
    assert data["accuracy_percentage"] == 80.0
    assert data["tests_completed"] == 2
    assert data["study_hours"] == 3.0  # 10800 seconds / 3600


def test_get_streak_data_endpoint_exists(mock_dependencies):
    """Test that the /api/dashboard/streak endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    
    response = client.get("/api/dashboard/streak")
    
    assert response.status_code == 200
    data = response.json()
    assert "current_streak" in data
    assert "streak_milestone_reached" in data


def test_get_streak_data_milestone_detection(mock_dependencies):
    """Test that streak milestones (7, 14, 30 days) are detected correctly"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock 7 consecutive days of activity
    today = datetime.utcnow().date()
    activity_data = [
        {"date": (today - timedelta(days=i)).isoformat(), "questions_solved": 5}
        for i in range(7)
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = activity_data
    
    response = client.get("/api/dashboard/streak")
    
    assert response.status_code == 200
    data = response.json()
    assert data["current_streak"] == 7
    assert data["streak_milestone_reached"] == True
    assert data["milestone_value"] == 7


def test_get_subject_performance_endpoint_exists(mock_dependencies):
    """Test that the /api/dashboard/subjects endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    response = client.get("/api/dashboard/subjects")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_subject_performance_aggregates_by_subject(mock_dependencies):
    """Test that subject performance aggregates topics correctly"""
    mock_supabase = mock_dependencies["supabase"]
    
    mastery_data = [
        {
            "subject": "Mathematics",
            "subject_id": "math",
            "questions_attempted": 10,
            "questions_correct": 8,
            "mastery_score": 80,
        },
        {
            "subject": "Mathematics",
            "subject_id": "math",
            "questions_attempted": 20,
            "questions_correct": 16,
            "mastery_score": 85,
        },
        {
            "subject": "Physics",
            "subject_id": "physics",
            "questions_attempted": 15,
            "questions_correct": 12,
            "mastery_score": 75,
        },
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mastery_data
    
    response = client.get("/api/dashboard/subjects")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 2 subjects
    assert len(data) == 2
    
    # Find math subject
    math_subject = next(s for s in data if s["subject_id"] == "math")
    assert math_subject["subject_name"] == "Mathematics"
    assert math_subject["questions_solved"] == 30  # 10 + 20
    assert math_subject["accuracy_percentage"] == 80.0  # (8+16)/(10+20) * 100
    assert math_subject["trend"] in ["up", "down", "flat"]


def test_get_recent_activity_endpoint_exists(mock_dependencies):
    """Test that the /api/dashboard/activity endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    
    response = client.get("/api/dashboard/activity")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_recent_activity_limits_to_5(mock_dependencies):
    """Test that recent activity returns maximum 5 items"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock 10 test completions
    tests_data = [
        {
            "id": f"test_{i}",
            "title": f"Test {i}",
            "score": 80 + i,
            "completed_at": datetime.utcnow().isoformat(),
            "status": "completed",
        }
        for i in range(10)
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = tests_data
    
    response = client.get("/api/dashboard/activity")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should return maximum 5 items
    assert len(data) <= 5


def test_get_full_dashboard_data_endpoint_exists(mock_dependencies):
    """Test that the /api/dashboard/full endpoint exists and returns complete data"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock all required data
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    
    response = client.get("/api/dashboard/full")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all required fields are present
    assert "user_id" in data
    assert "current_streak" in data
    assert "streak_milestone_reached" in data
    assert "key_metrics" in data
    assert "recent_activity" in data
    assert "subject_performance" in data
    assert "upcoming_tests" in data
    assert "recommendation" in data
    assert "data_timestamp" in data


def test_dashboard_data_freshness(mock_dependencies):
    """Test that dashboard data includes timestamp for freshness validation"""
    mock_supabase = mock_dependencies["supabase"]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.order.return_value.execute.return_value.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.eq.return_value.order.return_value.limit.return_value.execute.return_value.data = []
    
    response = client.get("/api/dashboard/full")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify timestamp is present and recent
    assert "data_timestamp" in data
    timestamp = datetime.fromisoformat(data["data_timestamp"].replace("Z", "+00:00"))
    now = datetime.utcnow()
    time_diff = (now - timestamp).total_seconds()
    
    # Data should be fresh (within 5 minutes as per requirements)
    assert time_diff < 300  # 5 minutes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
