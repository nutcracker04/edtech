"""
Tests for Recommendations API endpoint
Validates that the recommendations endpoint generates personalized recommendations
"""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch
from datetime import datetime, timedelta, timezone

from app.main import app
from app.utils.auth import get_current_user


# Mock user for authentication
def mock_get_current_user():
    return {"user_id": "test_user_123"}


# Mock authentication and supabase for all tests
@pytest.fixture(autouse=True)
def mock_dependencies():
    # Override the authentication dependency
    app.dependency_overrides[get_current_user] = mock_get_current_user
    
    with patch("app.routers.analysis.supabase") as mock_supabase:
        yield {"supabase": mock_supabase}
    
    # Clean up
    app.dependency_overrides.clear()


client = TestClient(app)


def test_recommendations_endpoint_exists(mock_dependencies):
    """Test that the /api/analysis/recommendations endpoint exists"""
    mock_supabase = mock_dependencies["supabase"]
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = []
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)


def test_recommendations_for_weak_topics(mock_dependencies):
    """Test that recommendations are generated for weak topics"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topic mastery data with weak topics
    mastery_data = [
        {
            "topic": "Algebra",
            "subject": "Mathematics",
            "mastery_score": 45.0,
            "last_attempt_date": datetime.now(timezone.utc).isoformat(),
        },
        {
            "topic": "Geometry",
            "subject": "Mathematics",
            "mastery_score": 85.0,
            "last_attempt_date": datetime.now(timezone.utc).isoformat(),
        },
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mastery_data
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have at least one recommendation for weak topic
    assert len(data) > 0
    
    # Find the focus recommendation
    focus_rec = next((r for r in data if r["type"] == "focus"), None)
    assert focus_rec is not None
    assert focus_rec["priority"] == "high"
    assert "Algebra" in focus_rec["title"]


def test_recommendations_for_strong_topics(mock_dependencies):
    """Test that motivational recommendations are generated for strong topics"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topic mastery data with strong topics
    mastery_data = [
        {
            "topic": "Algebra",
            "subject": "Mathematics",
            "mastery_score": 90.0,
            "last_attempt_date": datetime.now(timezone.utc).isoformat(),
        },
        {
            "topic": "Geometry",
            "subject": "Mathematics",
            "mastery_score": 88.0,
            "last_attempt_date": datetime.now(timezone.utc).isoformat(),
        },
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mastery_data
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have challenge recommendation
    challenge_rec = next((r for r in data if r["type"] == "challenge"), None)
    assert challenge_rec is not None
    assert challenge_rec["priority"] == "low"


def test_recommendations_for_inactive_topics(mock_dependencies):
    """Test that recommendations are generated for inactive topics"""
    mock_supabase = mock_dependencies["supabase"]
    
    # Mock topic mastery data with inactive topics (last attempted > 7 days ago)
    old_date = (datetime.now(timezone.utc) - timedelta(days=10)).isoformat()
    mastery_data = [
        {
            "topic": f"Topic {i}",
            "subject": "Mathematics",
            "mastery_score": 75.0,
            "last_attempt_date": old_date,
        }
        for i in range(5)  # 5 inactive topics
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mastery_data
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    
    # Should have practice recommendation for inactive topics
    practice_rec = next((r for r in data if r["type"] == "practice"), None)
    assert practice_rec is not None
    assert practice_rec["priority"] == "medium"


def test_recommendations_include_required_fields(mock_dependencies):
    """Test that recommendations include all required fields"""
    mock_supabase = mock_dependencies["supabase"]
    
    mastery_data = [
        {
            "topic": "Algebra",
            "subject": "Mathematics",
            "mastery_score": 45.0,
            "last_attempt_date": datetime.now(timezone.utc).isoformat(),
        },
    ]
    
    mock_supabase.table.return_value.select.return_value.eq.return_value.execute.return_value.data = mastery_data
    
    response = client.get("/api/analysis/recommendations")
    
    assert response.status_code == 200
    data = response.json()
    
    # Verify each recommendation has required fields
    for rec in data:
        assert "type" in rec
        assert "priority" in rec
        assert "title" in rec
        assert "description" in rec
        assert "action_url" in rec


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

