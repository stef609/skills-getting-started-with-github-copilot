"""
Integration tests for the FastAPI activity management application.

Tests cover all endpoints with happy paths, error cases, and edge cases including:
- Signup validation (duplicate prevention, capacity limits)
- Unregister functionality
- Activity listing and root redirect
"""

import pytest


class TestRootEndpoint:
    """Tests for the root endpoint."""
    
    def test_root_redirects_to_static(self, client):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for the GET /activities endpoint."""
    
    def test_get_activities_returns_all_activities(self, client):
        """Test that GET /activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Gym Class" in data
        assert len(data) == 3
    
    def test_get_activities_includes_correct_data(self, client):
        """Test that activities include all required fields"""
        response = client.get("/activities")
        data = response.json()
        
        activity = data["Chess Club"]
        assert activity["description"] == "Learn strategies and compete in chess tournaments"
        assert activity["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert activity["max_participants"] == 12
        assert isinstance(activity["participants"], list)
    
    def test_get_activities_shows_current_participants(self, client):
        """Test that activities show currently registered participants"""
        response = client.get("/activities")
        data = response.json()
        
        chess_participants = data["Chess Club"]["participants"]
        assert "michael@mergington.edu" in chess_participants
        assert "daniel@mergington.edu" in chess_participants
        assert len(chess_participants) == 2


class TestSignup:
    """Tests for the POST /activities/{activity_name}/signup endpoint."""
    
    def test_signup_successful(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Signed up" in data["message"]
        assert "newstudent@mergington.edu" in data["message"]
        assert "Chess Club" in data["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds participant to the activity"""
        client.post(
            "/activities/Chess%20Club/signup?email=newstudent@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "newstudent@mergington.edu" in participants
        assert len(participants) == 3
    
    def test_signup_duplicate_rejected(self, client):
        """Test that duplicate signup is rejected"""
        response = client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "already" in data["detail"].lower() or "signed up" in data["detail"].lower()
    
    def test_signup_duplicate_count_unchanged(self, client):
        """Test that duplicate signup attempt doesn't add person twice"""
        client.post(
            "/activities/Chess%20Club/signup?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        # Should still have original 2 participants
        assert len(participants) == 2
    
    def test_signup_activity_not_found(self, client):
        """Test signup for non-existent activity returns 404"""
        response = client.post(
            "/activities/NonExistent%20Club/signup?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_signup_capacity_exceeded(self, client):
        """Test signup when activity is at max capacity"""
        # Gym Class has max 2, currently has 1
        # Add one more to reach capacity
        client.post(
            "/activities/Gym%20Class/signup?email=student1@mergington.edu"
        )
        
        # Try to add another - should fail
        response = client.post(
            "/activities/Gym%20Class/signup?email=student2@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "capacity" in data["detail"].lower() or "maximum" in data["detail"].lower()
    
    def test_signup_capacity_exactly_at_limit(self, client):
        """Test signup when activity has exactly one spot left"""
        # Programming Class has max 3, currently has 1 (emma@mergington.edu)
        # Add two more to fill it exactly
        response1 = client.post(
            "/activities/Programming%20Class/signup?email=student1@mergington.edu"
        )
        assert response1.status_code == 200
        
        response2 = client.post(
            "/activities/Programming%20Class/signup?email=student2@mergington.edu"
        )
        assert response2.status_code == 200
        
        # Verify it's full
        response = client.get("/activities")
        data = response.json()
        assert len(data["Programming Class"]["participants"]) == 3


class TestUnregister:
    """Tests for the DELETE /activities/{activity_name}/unregister endpoint."""
    
    def test_unregister_successful(self, client):
        """Test successful unregister from an activity"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        assert response.status_code == 200
        data = response.json()
        assert "Unregistered" in data["message"]
        assert "michael@mergington.edu" in data["message"]
    
    def test_unregister_removes_participant(self, client):
        """Test that unregister actually removes participant from activity"""
        client.delete(
            "/activities/Chess%20Club/unregister?email=michael@mergington.edu"
        )
        
        response = client.get("/activities")
        data = response.json()
        participants = data["Chess Club"]["participants"]
        
        assert "michael@mergington.edu" not in participants
        assert len(participants) == 1
        assert "daniel@mergington.edu" in participants
    
    def test_unregister_not_registered(self, client):
        """Test unregister for participant not in activity returns 400"""
        response = client.delete(
            "/activities/Chess%20Club/unregister?email=notregistered@mergington.edu"
        )
        assert response.status_code == 400
        data = response.json()
        assert "not registered" in data["detail"].lower()
    
    def test_unregister_activity_not_found(self, client):
        """Test unregister from non-existent activity returns 404"""
        response = client.delete(
            "/activities/NonExistent%20Club/unregister?email=student@mergington.edu"
        )
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    
    def test_unregister_frees_up_capacity(self, client):
        """Test that unregistering frees up a spot for new signups"""
        # Gym Class is at capacity (max 2, has 1)
        client.post(
            "/activities/Gym%20Class/signup?email=student1@mergington.edu"
        )
        
        # Try to add another - should fail (at capacity)
        response = client.post(
            "/activities/Gym%20Class/signup?email=student2@mergington.edu"
        )
        assert response.status_code == 400
        
        # Unregister one participant
        client.delete(
            "/activities/Gym%20Class/unregister?email=john@mergington.edu"
        )
        
        # Now signup should succeed
        response = client.post(
            "/activities/Gym%20Class/signup?email=student2@mergington.edu"
        )
        assert response.status_code == 200


class TestIntegrationScenarios:
    """Integration tests combining multiple operations."""
    
    def test_signup_unregister_signup_cycle(self, client):
        """Test the full cycle: signup -> unregister -> signup again"""
        email = "test@mergington.edu"
        activity = "Chess%20Club"
        
        # Initial signup
        response1 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response1.status_code == 200
        
        # Verify added
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
        
        # Unregister
        response2 = client.delete(f"/activities/{activity}/unregister?email={email}")
        assert response2.status_code == 200
        
        # Verify removed
        response = client.get("/activities")
        assert email not in response.json()["Chess Club"]["participants"]
        
        # Signup again
        response3 = client.post(f"/activities/{activity}/signup?email={email}")
        assert response3.status_code == 200
        
        # Verify added again
        response = client.get("/activities")
        assert email in response.json()["Chess Club"]["participants"]
    
    def test_multiple_participants_management(self, client):
        """Test managing multiple participants in same activity"""
        activity = "Chess%20Club"
        emails = ["test1@test.edu", "test2@test.edu", "test3@test.edu"]
        
        # Signup multiple participants (Chess Club has max 12, starts with 2)
        for email in emails:
            response = client.post(
                f"/activities/{activity}/signup?email={email}"
            )
            assert response.status_code == 200
        
        # Verify all are added
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        for email in emails:
            assert email in participants
        
        # Unregister first participant
        response = client.delete(f"/activities/{activity}/unregister?email={emails[0]}")
        assert response.status_code == 200
        
        # Verify only first is removed
        response = client.get("/activities")
        participants = response.json()["Chess Club"]["participants"]
        assert emails[0] not in participants
        assert emails[1] in participants
        assert emails[2] in participants
