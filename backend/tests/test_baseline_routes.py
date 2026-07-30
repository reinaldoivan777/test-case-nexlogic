def test_health_endpoint_returns_ok(client):
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok"}


def test_knowledge_bases_returns_seed_data(client):
    response = client.get("/api/knowledge-bases")

    body = response.get_json()
    assert response.status_code == 200
    assert len(body["data"]) == 1
    assert body["data"][0]["id"] == "nexlogic-handbook"
