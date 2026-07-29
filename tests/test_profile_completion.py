from app.services.profile import calculate_profile_completion
from app.models.volunteer import VolunteerProfile
from tests.conftest import register_and_login, auth_header

def test_empty_profile_completion():
    assert calculate_profile_completion(None) == 0

def test_partial_profile_completion():
    p = VolunteerProfile(
        first_name="Test",
        last_name="User"
    )
    assert calculate_profile_completion(p) == 33

def test_whitespace_profile_completion():
    p = VolunteerProfile(
        first_name="Test",
        last_name="User",
        city="   ",
        bio="\n\t",
        skills="   ,  ",
        interests=" "
    )
    assert calculate_profile_completion(p) == 33

def test_complete_profile_completion():
    p = VolunteerProfile(
        first_name="Test",
        last_name="User",
        city="Istanbul",
        bio="Hello",
        skills="Python, React",
        interests="AI, Open Source"
    )
    assert calculate_profile_completion(p) == 100

def test_api_profile_completion_after_update(client):
    token = register_and_login(client, 'vol10@briva.org', 'volunteer')
    
    # Create partial profile
    res = client.put('/api/volunteers/me', json={'first_name': 'Test', 'last_name': 'User'}, headers=auth_header(token))
    assert res.status_code == 201
    assert res.json['volunteer']['profile_completion_percentage'] == 33

    # Update profile to be 100%
    data = {
        'city': 'Istanbul',
        'bio': 'Developer',
        'skills': 'Python',
        'interests': 'Tech'
    }
    res = client.put('/api/volunteers/me', json=data, headers=auth_header(token))
    assert res.status_code == 200
    assert res.json['volunteer']['profile_completion_percentage'] == 100
