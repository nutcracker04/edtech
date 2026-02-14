"""
Tests for Analysis Page API endpoints
Validates that all required endpoints are implemented correctly
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch
from datetime import datetime, timedelta

from app.main import app
from app.utils.auth import get_current_user
from app.models.analysis import (
    PerformanceOverview,
    TrendData,
    TrendDataPoint,
    WeakArea,
    SubjectBreakdown,
    TopicData,
    AnalysisRecommendation,
    AnalysisData,
)


# Mock user for authentication
def mock_get_current_user():
    return {"user_id": "test_user_123", "email": "test@example.com"}


# Override the dependency
app.dependency_overrides[get_current_user] = mock_get_current_user


# Mock authentication for all tests
@pytest.fixture(autouse=True)
def mock_dependencies():
    with patch("app.routers.analysis_page.supabase") as mock_supabase:
        yield {"supabase": mock_supabase}


client = TestClient(app)


def test_get_performance_overview_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/overview endpoint exists and returns correct structure"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock empty data
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/overview")
    
    # Should return 200 OK
    assert response.status_code == 200
    
    # Should have correct structure
    data = response.json()
    assert "accuracy_percentage" in data
    assert "questions_solved" in data
    assert "study_hours" in data
    assert "avg_time_per_question" in data


def test_get_performance_overview_calculates_correctly(mock_dependencies):
    """Test that overview metrics are calculated correctly"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topic mastery data
    mastery_data = [
        {"questions_attempted": 10, "questions_correct": 8, "last_attempt_date": "2024-01-15"},
        {"questions_attempted": 20, "questions_correct": 16, "last_attempt_date": "2024-01-16"},
    ]
    
    # Mock test attempts data
    attempts_data = [
        {"time_spent": 3600, "created_at": "2024-01-15T10:00:00"},  # 1 hour
        {"time_spent": 7200, "created_at": "2024-01-16T10:00:00"},  # 2 hours
    ]
    
    # Setup mock chain with proper chaining
    def mock_table(table_name):
        mock_chain = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_result = Mock()
        
        if table_name == "topic_mastery":
            mock_result.data = mastery_data
        elif table_name == "test_attempts":
            mock_result.data = attempts_data
        else:
            mock_result.data = []
        
        mock_eq.execute.return_value = mock_result
        mock_select.eq.return_value = mock_eq
        mock_chain.select.return_value = mock_select
        return mock_chain
    
    mock_supabase.table.side_effect = mock_table
    
    response = client.get("/api/analysis/overview?time_period=30d")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify calculations
    # Total questions: 10 + 20 = 30
    # Total correct: 8 + 16 = 24
    # Accuracy: 24/30 * 100 = 80%
    assert data["questions_solved"] == 30
    assert data["accuracy_percentage"] == 80.0
    assert data["study_hours"] == 3.0  # 10800 seconds / 3600
    assert data["avg_time_per_question"] == 360.0  # 10800 / 30


def test_get_performance_overview_supports_time_periods(mock_dependencies):
    """Test that overview endpoint supports different time periods"""
    mock_supabase = mock_dependencies["supabase"]
    
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    # Test different time periods
    for period in ['7d', '30d', '90d', 'all']:
        response = client.get(f"/api/analysis/overview?time_period={period}")
        assert response.status_code == 200


def test_get_trend_data_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/trends endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/trends")
    
    assert response.status_code == 200
    data = response.json()
    assert "accuracy_by_date" in data
    assert "questions_by_date" in data


def test_get_trend_data_groups_by_date(mock_dependencies):
    """Test that trend data is correctly grouped by date"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock test attempts over multiple days
    attempts_data = [
        {"created_at": "2024-01-15T10:00:00", "is_correct": True},
        {"created_at": "2024-01-15T11:00:00", "is_correct": True},
        {"created_at": "2024-01-15T12:00:00", "is_correct": False},
        {"created_at": "2024-01-16T10:00:00", "is_correct": True},
        {"created_at": "2024-01-16T11:00:00", "is_correct": True},
    ]
    
    # Setup mock chain properly
    mock_chain = Mock()
    mock_select = Mock()
    mock_eq = Mock()
    mock_result = Mock()
    mock_result.data = attempts_data
    mock_eq.execute.return_value = mock_result
    mock_select.eq.return_value = mock_eq
    mock_chain.select.return_value = mock_select
    mock_supabase.table.return_value = mock_chain
    
    response = client.get("/api/analysis/trends?time_period=30d")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 2 days of data
    assert len(data["accuracy_by_date"]) == 2
    assert len(data["questions_by_date"]) == 2
    
    # First day: 2 correct out of 3 = 66.67%
    assert data["accuracy_by_date"][0]["accuracy"] == pytest.approx(66.67, rel=0.01)
    assert data["questions_by_date"][0]["count"] == 3
    
    # Second day: 2 correct out of 2 = 100%
    assert data["accuracy_by_date"][1]["accuracy"] == 100.0
    assert data["questions_by_date"][1]["count"] == 2


def test_get_weak_areas_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/weak-areas endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.lt.return_value.order.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/weak-areas")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_weak_areas_ranks_by_impact(mock_dependencies):
    """Test that weak areas are ranked by impact score"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock weak topics with different impact levels
    weak_topics = [
        {
            "id": "topic1",
            "topic": "Algebra",
            "questions_attempted": 50,
            "questions_correct": 20,
            "mastery_score": 40,
        },
        {
            "id": "topic2",
            "topic": "Geometry",
            "questions_attempted": 30,
            "questions_correct": 15,
            "mastery_score": 50,
        },
        {
            "id": "topic3",
            "topic": "Calculus",
            "questions_attempted": 100,
            "questions_correct": 30,
            "mastery_score": 30,
        },
    ]
    
    mock_result = Mock()
    mock_result.data = weak_topics
    mock_supabase.table.return_value.select.return_value.eq.return_value.lt.return_value.order.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/weak-areas")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 3 weak areas
    assert len(data) == 3
    
    # Each should have required fields
    for area in data:
        assert "topic_id" in area
        assert "topic_name" in area
        assert "accuracy_percentage" in area
        assert "impact_score" in area
        assert "recommended_action" in area
    
    # Should be sorted by impact score (descending)
    assert data[0]["impact_score"] >= data[1]["impact_score"]
    assert data[1]["impact_score"] >= data[2]["impact_score"]


def test_get_subject_breakdown_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/subjects endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/subjects")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_subject_breakdown_groups_topics_by_subject(mock_dependencies):
    """Test that subject breakdown correctly groups topics by subject"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topic mastery data with multiple subjects
    mastery_data = [
        {
            "id": "topic1",
            "subject": "Mathematics",
            "subject_id": "math",
            "topic": "Algebra",
            "questions_attempted": 10,
            "questions_correct": 8,
            "mastery_score": 80,
        },
        {
            "id": "topic2",
            "subject": "Mathematics",
            "subject_id": "math",
            "topic": "Geometry",
            "questions_attempted": 20,
            "questions_correct": 16,
            "mastery_score": 85,
        },
        {
            "id": "topic3",
            "subject": "Physics",
            "subject_id": "physics",
            "topic": "Mechanics",
            "questions_attempted": 15,
            "questions_correct": 12,
            "mastery_score": 75,
        },
    ]
    
    mock_result = Mock()
    mock_result.data = mastery_data
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/subjects")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have 2 subjects
    assert len(data) == 2
    
    # Find math subject
    math_subject = next(s for s in data if s["subject_id"] == "math")
    assert math_subject["subject_name"] == "Mathematics"
    assert math_subject["questions_solved"] == 30  # 10 + 20
    assert math_subject["accuracy_percentage"] == 80.0  # (8+16)/(10+20) * 100
    assert len(math_subject["topics"]) == 2
    assert math_subject["trend"] in ["up", "down", "flat"]
    
    # Verify topic structure
    for topic in math_subject["topics"]:
        assert "topic_id" in topic
        assert "topic_name" in topic
        assert "accuracy_percentage" in topic
        assert "questions_solved" in topic
        assert "trend" in topic


def test_get_analysis_recommendations_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/recommendations endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Setup mock chain properly
    mock_chain = Mock()
    mock_select = Mock()
    mock_eq = Mock()
    mock_result = Mock()
    mock_result.data = []
    mock_eq.execute.return_value = mock_result
    mock_select.eq.return_value = mock_eq
    mock_chain.select.return_value = mock_select
    mock_supabase.table.return_value = mock_chain
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_get_analysis_recommendations_prioritizes_weak_areas(mock_dependencies):
    """Test that recommendations prioritize weak areas"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topics with varying mastery scores
    topics_data = [
        {
            "id": "topic1",
            "topic": "Algebra",
            "questions_attempted": 50,
            "questions_correct": 15,
            "mastery_score": 30,
        },
        {
            "id": "topic2",
            "topic": "Geometry",
            "questions_attempted": 30,
            "questions_correct": 18,
            "mastery_score": 60,
        },
        {
            "id": "topic3",
            "topic": "Calculus",
            "questions_attempted": 40,
            "questions_correct": 36,
            "mastery_score": 90,
        },
    ]
    
    # Setup mock chain properly
    mock_chain = Mock()
    mock_select = Mock()
    mock_eq = Mock()
    mock_result = Mock()
    mock_result.data = topics_data
    mock_eq.execute.return_value = mock_result
    mock_select.eq.return_value = mock_eq
    mock_chain.select.return_value = mock_select
    mock_supabase.table.return_value = mock_chain
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have recommendations for weak topics (mastery < 70)
    assert len(data) >= 1
    
    # Each recommendation should have required fields
    for rec in data:
        assert "topic_id" in rec
        assert "topic_name" in rec
        assert "reason" in rec
        assert "action" in rec
        assert "difficulty" in rec
        assert "estimated_time_minutes" in rec
        assert "priority" in rec
        assert rec["priority"] in ["high", "medium", "low"]


def test_get_full_analysis_data_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/full endpoint exists and returns complete data"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock all required data
    mock_result = Mock()
    mock_result.data = []
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value = mock_result
    mock_supabase.table.return_value.select.return_value.eq.return_value.lt.return_value.order.return_value.execute.return_value = mock_result
    
    response = client.get("/api/analysis/full")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify all required fields are present
    assert "user_id" in data
    assert "time_period" in data
    assert "performance_overview" in data
    assert "subject_performance" in data
    assert "trend_data" in data
    assert "weak_areas" in data
    assert "recommendations" in data
    assert "data_timestamp" in data


def test_analysis_data_freshness(mock_dependencies):
    """Test that analysis data includes timestamp for freshness validation"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Setup mock chain properly for all tables
    def mock_table_chain(table_name):
        mock_chain = Mock()
        mock_select = Mock()
        mock_eq = Mock()
        mock_lt = Mock()
        mock_order = Mock()
        mock_result = Mock()
        mock_result.data = []
        
        # Chain for weak areas (has .lt())
        mock_order.execute.return_value = mock_result
        mock_lt.order.return_value = mock_order
        mock_eq.lt.return_value = mock_lt
        
        # Chain for regular queries
        mock_eq.execute.return_value = mock_result
        mock_select.eq.return_value = mock_eq
        mock_chain.select.return_value = mock_select
        return mock_chain
    
    mock_supabase.table.side_effect = mock_table_chain
    
    response = client.get("/api/analysis/full")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify timestamp is present and recent
    assert "data_timestamp" in data
    timestamp_str = data["data_timestamp"]
    
    # Parse the timestamp (handle both with and without 'Z')
    if timestamp_str.endswith('Z'):
        timestamp_str = timestamp_str[:-1] + '+00:00'
    
    timestamp = datetime.fromisoformat(timestamp_str)
    now = datetime.now(timestamp.tzinfo) if timestamp.tzinfo else datetime.now()
    time_diff = abs((now - timestamp).total_seconds())
    
    # Data should be fresh (within 5 minutes as per requirements)
    assert time_diff < 300  # 5 minutes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
