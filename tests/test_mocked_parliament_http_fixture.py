"""
Test the mocked_parliament_http fixture.

This test validates that the fixture correctly mocks HTTP requests
and prevents real network calls.
"""

from bs4 import BeautifulSoup


def test_mocked_parliament_http_provides_realistic_html(mocked_parliament_http):
    """
    Test that mocked_parliament_http provides realistic HTML.
    
    Validates: Requirements 4.1, 4.4, 4.5
    """
    # Get the mock response
    response = mocked_parliament_http.get('https://parliament.go.ke/hansard')
    
    # Verify response attributes
    assert response.status_code == 200
    assert response.text is not None
    assert len(response.text) > 0
    
    # Verify HTML structure
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # Should contain PDF links
    pdf_links = soup.find_all('a', href=lambda h: h and '.pdf' in h.lower())
    assert len(pdf_links) > 0, "Mock HTML should contain PDF links"
    
    # Should contain British date formats
    assert 'December 2025' in response.text
    assert 'October 2025' in response.text


def test_mocked_parliament_http_prevents_real_calls(mocked_parliament_http):
    """
    Test that the fixture prevents real network calls.
    
    Validates: Requirements 4.2, 4.3
    """
    # The fixture should have mocked requests.Session
    # Any call to get() should return the mock response
    response = mocked_parliament_http.get('https://any-url.com')
    
    # Should get the mocked response, not a real network call
    assert response.status_code == 200
    assert 'Hansard' in response.text
    
    # Verify the mock was called
    assert mocked_parliament_http.get.called
    assert mocked_parliament_http.get.call_count >= 1


def test_mocked_parliament_http_response_structure(mocked_parliament_http):
    """
    Test that mock response has correct structure.
    
    Validates: Requirements 4.5
    """
    response = mocked_parliament_http.get('https://parliament.go.ke/hansard')
    
    # Verify response has expected attributes
    assert hasattr(response, 'text')
    assert hasattr(response, 'status_code')
    assert hasattr(response, 'raise_for_status')
    
    # Verify raise_for_status is callable
    assert callable(response.raise_for_status)
    
    # Should not raise an exception for successful response
    response.raise_for_status()  # Should not raise


def test_mocked_parliament_http_with_multiple_calls(mocked_parliament_http):
    """
    Test that fixture works with multiple HTTP calls.
    
    Validates: Requirements 4.1
    """
    # Make multiple calls
    response1 = mocked_parliament_http.get('https://parliament.go.ke/hansard?page=0')
    response2 = mocked_parliament_http.get('https://parliament.go.ke/hansard?page=1')
    response3 = mocked_parliament_http.get('https://parliament.go.ke/hansard?page=2')
    
    # All should return the same mock response
    assert response1.text == response2.text == response3.text
    assert response1.status_code == response2.status_code == response3.status_code
    
    # Verify call count
    assert mocked_parliament_http.get.call_count == 3
