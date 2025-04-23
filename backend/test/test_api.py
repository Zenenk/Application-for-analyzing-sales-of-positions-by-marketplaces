def test_get_items(client):
    response = client.get('/api/items', headers={'Authorization': 'Bearer your_api_token_here'})
    assert response.status_code == 200
