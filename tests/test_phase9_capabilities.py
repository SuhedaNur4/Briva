from tests.conftest import auth_header, register_and_login

def _setup_org(client, email="org_p9@briva.com", name="P9 STK"):
    token = register_and_login(client, email, role="organization")
    res = client.post(
        "/api/organizations",
        json={"name": name, "city": "İstanbul"},
        headers=auth_header(token),
    )
    return token, res.get_json()["organization"]["id"]

def _setup_vol(client, email="vol_p9@briva.com"):
    token = register_and_login(client, email, role="volunteer")
    client.put(
        "/api/volunteers/me",
        json={
            "first_name": "Ali",
            "last_name": "Yılmaz",
            "city": "İstanbul",
            "bio": "Sosyal etki yaratmayı seven bir geliştirici.",
            "skills": "Web Geliştirme, Python, İletişim",
            "interests": "Teknoloji, Eğitim"
        },
        headers=auth_header(token),
    )
    res = client.get("/api/auth/me", headers=auth_header(token))
    return token, res.get_json()["user"]["id"]

def test_p0_applicant_detail_profile(client):
    org_token, org_id = _setup_org(client, "org_detail@briva.com")
    ev_res = client.post(
        "/api/events",
        json={"title": "Web Atölyesi", "start_date": "2026-11-11T10:00:00", "city": "İstanbul"},
        headers=auth_header(org_token),
    )
    ev_id = ev_res.get_json()["event"]["id"]

    vol_token, vol_id = _setup_vol(client, "vol_detail@briva.com")
    client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "Bu atölyede yer almak istiyorum."},
        headers=auth_header(vol_token),
    )

    apps_res = client.get(f"/api/events/{ev_id}/applications", headers=auth_header(org_token))
    assert apps_res.status_code == 200
    data = apps_res.get_json()
    assert len(data["applications"]) == 1
    vol_data = data["applications"][0]["volunteer"]
    assert vol_data["city"] == "İstanbul"
    assert vol_data["bio"] == "Sosyal etki yaratmayı seven bir geliştirici."
    assert "Web Geliştirme" in vol_data["skills"]
    assert "Teknoloji" in vol_data["interests"]

def test_p0_evaluate_applicant_explainability_and_real_data(client):
    org_token, org_id = _setup_org(client, "org_eval@briva.com")
    ev_res = client.post(
        "/api/events",
        json={
            "title": "Python Bootcamp Gönüllüsü",
            "start_date": "2026-11-15T10:00:00",
            "city": "İstanbul",
            "category": "Teknoloji",
            "requirements": "Python, İletişim"
        },
        headers=auth_header(org_token),
    )
    ev_id = ev_res.get_json()["event"]["id"]

    vol_token, vol_id = _setup_vol(client, "vol_eval@briva.com")
    app_res = client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "Başvuru"},
        headers=auth_header(vol_token),
    )
    app_id = app_res.get_json()["application"]["id"]

    eval_res = client.post(
        "/api/recommendations/evaluate-applicant",
        json={"application_id": app_id},
        headers=auth_header(org_token),
    )
    assert eval_res.status_code == 200
    eval_data = eval_res.get_json()
    assert "evaluation" in eval_data
    ev = eval_data["evaluation"]
    assert ev["city_match"] is True
    assert "Python" in ev["matching_skills"]
    assert "Teknoloji" in ev["matching_interests"]
    assert "score" not in ev
    assert "percentage" not in ev
    assert len(ev["reasons"]) >= 2
    assert "örtüşüyor" in ev["reasons"][0]

def test_p0_evaluate_applicant_role_security_gates(client):
    org_token_a, org_id_a = _setup_org(client, "org_sec_a@briva.com", "Org A")
    org_token_b, org_id_b = _setup_org(client, "org_sec_b@briva.com", "Org B")
    ev_res = client.post(
        "/api/events",
        json={"title": "Gizli Etkinlik", "start_date": "2026-11-20T10:00:00"},
        headers=auth_header(org_token_a),
    )
    ev_id = ev_res.get_json()["event"]["id"]

    vol_token, vol_id = _setup_vol(client, "vol_sec@briva.com")
    app_res = client.post(
        f"/api/events/{ev_id}/apply",
        json={"cover_letter": "Selam"},
        headers=auth_header(vol_token),
    )
    app_id = app_res.get_json()["application"]["id"]

    assert client.post("/api/recommendations/evaluate-applicant", json={"application_id": app_id}).status_code == 401

    assert client.post(
        "/api/recommendations/evaluate-applicant",
        json={"application_id": app_id},
        headers=auth_header(vol_token),
    ).status_code == 403

    assert client.post(
        "/api/recommendations/evaluate-applicant",
        json={"application_id": app_id},
        headers=auth_header(org_token_b),
    ).status_code == 403

def test_p1_organizations_me(client):
    assert client.get("/api/organizations/me").status_code == 401

    vol_token = register_and_login(client, "vol_me@briva.com", role="volunteer")
    assert client.get("/api/organizations/me", headers=auth_header(vol_token)).status_code == 403

    org_token = register_and_login(client, "org_no_prof@briva.com", role="organization")
    assert client.get("/api/organizations/me", headers=auth_header(org_token)).status_code == 404

    client.post("/api/organizations", json={"name": "Benim STK"}, headers=auth_header(org_token))
    res = client.get("/api/organizations/me", headers=auth_header(org_token))
    assert res.status_code == 200
    assert res.get_json()["organization"]["name"] == "Benim STK"

def test_p1_server_side_draft(client):
    org_token, org_id = _setup_org(client, "org_draft@briva.com")
    res = client.post(
        "/api/events",
        json={
            "title": "Taslak Etkinlik",
            "start_date": "2026-12-01T10:00:00",
            "status": "draft"
        },
        headers=auth_header(org_token),
    )
    assert res.status_code == 201
    ev_data = res.get_json()["event"]
    assert ev_data["status"] == "draft"
    ev_id = ev_data["id"]

    list_pub = client.get("/api/events")
    pub_ids = [e["id"] for e in list_pub.get_json()["events"]]
    assert ev_id not in pub_ids

    list_all = client.get(f"/api/events?organization_id={org_id}&status=all")
    all_ids = [e["id"] for e in list_all.get_json()["events"]]
    assert ev_id in all_ids
