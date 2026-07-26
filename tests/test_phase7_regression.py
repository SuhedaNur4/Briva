from tests.conftest import auth_header, register_and_login


def _setup_org(client, email="org_p7@briva.com"):
    token = register_and_login(client, email, role="organization")
    client.post(
        "/api/organizations",
        json={"name": "P7 STK", "city": "Ankara"},
        headers=auth_header(token),
    )
    return token


def _create_event(client, org_token, title="P7 Etkinlik"):
    res = client.post(
        "/api/events",
        json={"title": title, "start_date": "2026-10-10T10:00:00", "city": "Ankara"},
        headers=auth_header(org_token),
    )
    return res.get_json()["event"]["id"]


def test_protected_routes_without_token_returns_401(client):
    assert client.get("/api/auth/me").status_code == 401
    assert (
        client.post(
            "/api/events", json={"title": "Test", "start_date": "2026-10-10T10:00:00"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/organizations", json={"name": "Test Org"}
        ).status_code
        == 401
    )


def test_role_mismatch_volunteer_creating_event_returns_403(client):
    vol_token = register_and_login(
        client, "vol_p7_event@briva.com", role="volunteer"
    )
    res = client.post(
        "/api/events",
        json={"title": "Vol Event", "start_date": "2026-10-10T10:00:00"},
        headers=auth_header(vol_token),
    )
    assert res.status_code == 403
    assert "error" in res.get_json()


def test_role_mismatch_organization_applying_returns_403(client):
    org_token = _setup_org(client, "org_app_test@briva.com")
    ev_id = _create_event(client, org_token)
    res = client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "STK basvurusu"},
        headers=auth_header(org_token),
    )
    assert res.status_code == 403
    assert "error" in res.get_json()


def test_event_creation_validation_missing_fields_returns_400(client):
    org_token = _setup_org(client, "org_val_test@briva.com")
    res = client.post(
        "/api/events",
        json={"category": "cevre"},
        headers=auth_header(org_token),
    )
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_application_duplicate_handling_returns_409(client):
    org_token = _setup_org(client, "org_dup_test@briva.com")
    ev_id = _create_event(client, org_token)
    vol_token = register_and_login(
        client, "vol_dup_test@briva.com", role="volunteer"
    )
    res1 = client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "Ilk basvuru"},
        headers=auth_header(vol_token),
    )
    assert res1.status_code == 201
    res2 = client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "Ikinci basvuru"},
        headers=auth_header(vol_token),
    )
    assert res2.status_code == 409
    assert "error" in res2.get_json()


def test_organization_applicant_status_update(client):
    org_token = _setup_org(client, "org_status_test@briva.com")
    ev_id = _create_event(client, org_token)
    vol_token = register_and_login(
        client, "vol_status_test@briva.com", role="volunteer"
    )
    app_res = client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "Basvuru"},
        headers=auth_header(vol_token),
    )
    app_id = app_res.get_json()["application"]["id"]

    update_res = client.put(
        f"/api/applications/{app_id}",
        json={"status": "approved"},
        headers=auth_header(org_token),
    )
    assert update_res.status_code == 200
    assert update_res.get_json()["application"]["status"] == "approved"


def test_empty_api_responses(client):
    res = client.get("/api/events?q=nonexistentkeywordthatdefinitelydoesnotexist")
    assert res.status_code == 200
    body = res.get_json()
    assert "events" in body
    assert len(body["events"]) == 0
    assert body["pagination"]["total"] == 0


def test_api_error_response_format(client):
    res = client.post(
        "/api/auth/login",
        json={"email": "nobody@briva.com", "password": "ValidPass123!"},
    )
    assert res.status_code == 401
    assert "error" in res.get_json()

