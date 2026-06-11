"""
EcoTrace API — comprehensive test suite.

Built against the actual source code in Carbon_mapping-main:
  - app/__init__.py       (blueprints, /api/health)
  - app/routes/auth.py   (register, login, profile, refresh, delete account)
  - app/routes/goals.py  (CRUD + status endpoint)
  - app/routes/tracking.py (log, records, update record)
  - app/routes/dashboard.py (analytics aggregation)
  - app/routes/leaderboard.py (score / footprint modes)
  - app/routes/calculator.py (calculate, factors, quick)
  - app/routes/recommendations.py (POST /, GET /history)
  - app/routes/prediction.py
  - app/routes/reports.py (CSV, PDF, summary)
  - app/routes/offset.py

Run:
    pytest tests/test_app.py -v
    pytest tests/test_app.py -v --tb=short   # concise tracebacks
"""
import pytest
from app import create_app


# ── Constants ────────────────────────────────────────────────────────────────

TEST_USER = {
    "name": "Test User",
    "email": "testuser_ecotrace@example.com",
    "password": "TestPass@123",
    "city": "Mumbai",
    "country": "India",
}

SECONDARY_USER = {
    "name": "Secondary User",
    "email": "secondary_ecotrace@example.com",
    "password": "SecPass@123",
}

DUPLICATE_USER = {
    "name": "Dup User",
    "email": "dup_ecotrace@example.com",
    "password": "DupPass@123",
}

NONEXISTENT_ID = 999_999

# All valid transport modes from TRANSPORT_FACTORS in emission_calculator.py
TRANSPORT_MODES = [
    "petrol_car", "diesel_car", "cng_car", "electric_car",
    "bike", "bus", "train", "flight_short", "flight_long",
]

# All valid food types from FOOD_FACTORS
FOOD_TYPES = ["vegan", "vegetarian", "pescatarian", "non_veg"]


# ── Helpers ──────────────────────────────────────────────────────────────────

def assert_success(response, expected_status=200):
    """Assert a successful JSON response; return parsed body."""
    assert response.status_code == expected_status, (
        f"Expected HTTP {expected_status}, got {response.status_code}. "
        f"Body: {response.get_data(as_text=True)}"
    )
    body = response.get_json()
    assert body is not None, "Response body is not valid JSON"
    assert body.get("success") is True, (
        f"Expected success=True in response body, got: {body}"
    )
    return body


def assert_error(response, expected_status):
    """Assert an error response with the expected status code; return body."""
    assert response.status_code == expected_status, (
        f"Expected HTTP {expected_status}, got {response.status_code}. "
        f"Body: {response.get_data(as_text=True)}"
    )
    body = response.get_json()
    assert body is not None, "Error response body is not valid JSON"
    assert body.get("success") is False, (
        f"Expected success=False in error response, got: {body}"
    )
    return body


def bearer(token):
    return {"Authorization": f"Bearer {token}"}


# ── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def app():
    application = create_app()
    application.config.update({
        "TESTING": True,
        "SECRET_KEY": "test-secret",
        "JWT_SECRET_KEY": "test-jwt-secret",
    })
    yield application


@pytest.fixture(scope="session")
def client(app):
    return app.test_client()


@pytest.fixture(scope="session")
def auth_token(client):
    """Register (or login on duplicate) the primary test user; return access token."""
    resp = client.post("/api/auth/register", json=TEST_USER)
    if resp.status_code == 409:
        resp = client.post("/api/auth/login", json={
            "email": TEST_USER["email"],
            "password": TEST_USER["password"],
        })
    body = resp.get_json()
    assert body and "data" in body and "access_token" in body["data"], (
        f"Could not obtain auth token. Response: {body}"
    )
    return body["data"]["access_token"]


@pytest.fixture(scope="session")
def refresh_token(client):
    """Register (or login) and return the refresh token."""
    resp = client.post("/api/auth/register", json={
        "name": "Refresh User",
        "email": "refresh_ecotrace@example.com",
        "password": "RefPass@123",
    })
    if resp.status_code == 409:
        resp = client.post("/api/auth/login", json={
            "email": "refresh_ecotrace@example.com",
            "password": "RefPass@123",
        })
    body = resp.get_json()
    return body["data"]["refresh_token"]


@pytest.fixture(scope="session")
def auth_headers(auth_token):
    return bearer(auth_token)


# ── Health ───────────────────────────────────────────────────────────────────

class TestHealth:
    def test_get_returns_200(self, client):
        assert client.get("/api/health").status_code == 200

    def test_status_is_ok(self, client):
        body = client.get("/api/health").get_json()
        assert body["status"] == "ok", f"Unexpected status value: {body['status']}"

    def test_service_field_present(self, client):
        body = client.get("/api/health").get_json()
        assert "service" in body, "Health response missing 'service' field"

    def test_version_field_present(self, client):
        body = client.get("/api/health").get_json()
        assert "version" in body, "Health response missing 'version' field"

    def test_options_preflight_returns_204(self, client):
        # Defined explicitly in app/__init__.py as returning "", 204
        r = client.options("/api/health")
        assert r.status_code in (200, 204), (
            f"OPTIONS /api/health should return 204, got {r.status_code}"
        )


# ── Auth — Registration ───────────────────────────────────────────────────────

class TestAuthRegistration:
    def test_register_returns_201_and_tokens(self, client):
        r = client.post("/api/auth/register", json=SECONDARY_USER)
        # 201 on first call, 409 on repeated runs — both are acceptable
        assert r.status_code in (201, 409), (
            f"Unexpected status {r.status_code}: {r.get_data(as_text=True)}"
        )
        if r.status_code == 201:
            body = r.get_json()
            assert "access_token" in body["data"], "Register response missing access_token"
            assert "refresh_token" in body["data"], "Register response missing refresh_token"

    def test_register_duplicate_email_returns_409(self, client):
        client.post("/api/auth/register", json=DUPLICATE_USER)
        r = client.post("/api/auth/register", json=DUPLICATE_USER)
        body = assert_error(r, 409)
        assert "already" in body["message"].lower(), (
            f"409 message should mention duplicate: {body['message']}"
        )

    def test_register_missing_name_returns_422(self, client):
        assert_error(client.post("/api/auth/register", json={
            "email": "no_name@example.com", "password": "Pass@1234",
        }), 422)

    def test_register_missing_email_returns_422(self, client):
        assert_error(client.post("/api/auth/register", json={
            "name": "No Email", "password": "Pass@1234",
        }), 422)

    def test_register_missing_password_returns_422(self, client):
        assert_error(client.post("/api/auth/register", json={
            "name": "No Pass", "email": "no_pass@example.com",
        }), 422)

    def test_register_invalid_email_format_returns_422(self, client):
        # auth.py validates via EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
        assert_error(client.post("/api/auth/register", json={
            "name": "Bad Email", "email": "not-an-email", "password": "Pass@1234",
        }), 422)

    def test_register_short_password_returns_422(self, client):
        # auth.py enforces len(password) >= 8
        assert_error(client.post("/api/auth/register", json={
            "name": "Short", "email": "short_pw@example.com", "password": "abc",
        }), 422)

    def test_register_empty_body_returns_422(self, client):
        assert_error(client.post("/api/auth/register", json={}), 422)

    def test_register_response_excludes_password_hash(self, client):
        r = client.post("/api/auth/register", json={
            "name": "Safe User", "email": "safe_ecotrace@example.com",
            "password": "SafePass@123",
        })
        if r.status_code == 201:
            body = r.get_json()
            user_obj = body["data"]["user"]
            assert "password_hash" not in user_obj, (
                "password_hash must not appear in register response"
            )


# ── Auth — Login ──────────────────────────────────────────────────────────────

class TestAuthLogin:
    def test_login_returns_access_and_refresh_tokens(self, auth_token):
        assert auth_token and len(auth_token) > 20, (
            "access_token is missing or suspiciously short"
        )

    def test_login_wrong_password_returns_401(self, client):
        assert_error(client.post("/api/auth/login", json={
            "email": TEST_USER["email"], "password": "WrongPassword!",
        }), 401)

    def test_login_nonexistent_email_returns_401(self, client):
        assert_error(client.post("/api/auth/login", json={
            "email": "nobody@nowhere.com", "password": "SomePass@123",
        }), 401)

    def test_login_missing_password_returns_422(self, client):
        assert_error(client.post("/api/auth/login", json={
            "email": "only@email.com",
        }), 422)

    def test_login_missing_email_returns_422(self, client):
        assert_error(client.post("/api/auth/login", json={
            "password": "OnlyPass@123",
        }), 422)

    def test_login_empty_body_returns_422(self, client):
        assert_error(client.post("/api/auth/login", json={}), 422)

    def test_login_response_excludes_password_hash(self, client):
        r = client.post("/api/auth/login", json={
            "email": TEST_USER["email"], "password": TEST_USER["password"],
        })
        body = assert_success(r)
        assert "password_hash" not in body["data"]["user"], (
            "password_hash must not appear in login response"
        )


# ── Auth — Token Refresh ──────────────────────────────────────────────────────

class TestAuthRefresh:
    def test_refresh_with_valid_refresh_token(self, client, refresh_token):
        # /api/auth/refresh requires a refresh token (type="refresh" in JWT payload)
        r = client.post("/api/auth/refresh",
                        headers=bearer(refresh_token))
        body = assert_success(r)
        assert "access_token" in body["data"], "Refresh response missing access_token"

    def test_refresh_with_access_token_returns_401(self, client, auth_token):
        # jwt_required(refresh=True) checks payload["type"] == "refresh"
        r = client.post("/api/auth/refresh", headers=bearer(auth_token))
        assert_error(r, 401)

    def test_refresh_with_no_token_returns_401(self, client):
        assert_error(client.post("/api/auth/refresh"), 401)


# ── Auth — Profile ────────────────────────────────────────────────────────────

class TestAuthProfile:
    def test_get_profile_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/auth/profile", headers=auth_headers))

    def test_get_profile_contains_email(self, client, auth_headers):
        body = assert_success(client.get("/api/auth/profile", headers=auth_headers))
        assert "email" in body["data"], "Profile response missing 'email'"

    def test_get_profile_email_matches_registered(self, client, auth_headers):
        body = assert_success(client.get("/api/auth/profile", headers=auth_headers))
        assert body["data"]["email"] == TEST_USER["email"]

    def test_get_profile_no_token_returns_401(self, client):
        assert_error(client.get("/api/auth/profile"), 401)

    def test_get_profile_invalid_token_returns_401(self, client):
        assert_error(client.get("/api/auth/profile",
                                headers={"Authorization": "Bearer invalid.token.xyz"}), 401)

    def test_get_profile_malformed_header_returns_401(self, client):
        # jwt_required checks auth.startswith("Bearer ")
        assert_error(client.get("/api/auth/profile",
                                headers={"Authorization": "Token abc123"}), 401)

    def test_update_city_returns_200(self, client, auth_headers):
        body = assert_success(client.put("/api/auth/profile",
                                         json={"city": "Bangalore"},
                                         headers=auth_headers))
        assert body["data"]["city"] == "Bangalore", (
            "Updated city should be reflected in response"
        )

    def test_update_name_returns_200(self, client, auth_headers):
        body = assert_success(client.put("/api/auth/profile",
                                         json={"name": "Updated Name"},
                                         headers=auth_headers))
        assert body["data"]["name"] == "Updated Name"

    def test_update_password_too_short_returns_422(self, client, auth_headers):
        # auth.py: len(d["password"]) < 8 → 422
        assert_error(client.put("/api/auth/profile",
                                json={"password": "abc"},
                                headers=auth_headers), 422)

    def test_update_empty_body_returns_422(self, client, auth_headers):
        # auth.py: if not sets → 422 "Nothing to update."
        assert_error(client.put("/api/auth/profile", json={}, headers=auth_headers), 422)

    def test_update_profile_unauthenticated_returns_401(self, client):
        assert_error(client.put("/api/auth/profile", json={"city": "Chennai"}), 401)

    def test_get_profile_excludes_password_hash(self, client, auth_headers):
        body = assert_success(client.get("/api/auth/profile", headers=auth_headers))
        assert "password_hash" not in body["data"], (
            "password_hash must never appear in profile response"
        )


# ── Goals ─────────────────────────────────────────────────────────────────────

class TestGoals:
    @pytest.fixture(scope="class")
    def goal_id(self, client, auth_headers):
        r = client.post("/api/goals/", json={
            "title": "Fixture Goal",
            "target_value": 100,
            "category": "transport",
        }, headers=auth_headers)
        assert r.status_code == 201, (
            f"Failed to create fixture goal: {r.get_data(as_text=True)}"
        )
        return r.get_json()["data"]["id"]

    def test_create_goal_returns_201(self, client, auth_headers):
        r = client.post("/api/goals/", json={
            "title": "Cut Electricity", "target_value": 50,
        }, headers=auth_headers)
        assert r.status_code == 201

    def test_create_goal_response_has_correct_title(self, client, auth_headers):
        r = client.post("/api/goals/", json={
            "title": "My Goal", "target_value": 75,
        }, headers=auth_headers)
        assert r.get_json()["data"]["title"] == "My Goal"

    def test_create_goal_initial_achievement_pct_is_zero(self, client, auth_headers):
        r = client.post("/api/goals/", json={
            "title": "Zero Start", "target_value": 100,
        }, headers=auth_headers)
        assert r.get_json()["data"]["achievement_pct"] == 0.0, (
            "New goal with current_value=0 should have 0% achievement"
        )

    def test_create_goal_with_all_categories(self, client, auth_headers):
        for cat in ("transport", "electricity", "food", "fuel", "overall"):
            r = client.post("/api/goals/", json={
                "title": f"{cat} goal", "target_value": 10, "category": cat,
            }, headers=auth_headers)
            assert r.status_code == 201, f"Failed for category '{cat}'"

    def test_create_goal_with_valid_end_date(self, client, auth_headers):
        r = client.post("/api/goals/", json={
            "title": "Dated Goal", "target_value": 50,
            "end_date": "2030-12-31",
        }, headers=auth_headers)
        assert r.status_code == 201

    def test_create_goal_invalid_end_date_returns_422(self, client, auth_headers):
        # goals.py validates end_date via date.fromisoformat
        r = client.post("/api/goals/", json={
            "title": "Bad Date", "target_value": 50,
            "end_date": "not-a-date",
        }, headers=auth_headers)
        assert_error(r, 422)

    def test_create_goal_missing_title_returns_422(self, client, auth_headers):
        assert_error(client.post("/api/goals/",
                                 json={"target_value": 50},
                                 headers=auth_headers), 422)

    def test_create_goal_missing_target_returns_422(self, client, auth_headers):
        assert_error(client.post("/api/goals/",
                                 json={"title": "No Target"},
                                 headers=auth_headers), 422)

    def test_create_goal_unauthenticated_returns_401(self, client):
        assert_error(client.post("/api/goals/", json={
            "title": "Unauth", "target_value": 10,
        }), 401)

    def test_list_goals_returns_list(self, client, auth_headers):
        body = assert_success(client.get("/api/goals/", headers=auth_headers))
        assert isinstance(body["data"], list), "'data' should be a list"

    def test_get_goal_by_id(self, client, auth_headers, goal_id):
        body = assert_success(client.get(f"/api/goals/{goal_id}",
                                         headers=auth_headers))
        assert body["data"]["id"] == goal_id

    def test_get_goal_not_found_returns_404(self, client, auth_headers):
        assert_error(client.get(f"/api/goals/{NONEXISTENT_ID}",
                                headers=auth_headers), 404)

    def test_update_current_value_recalculates_achievement_pct(self, client, auth_headers, goal_id):
        # target=100, current=30 → 30.0%
        body = assert_success(client.put(f"/api/goals/{goal_id}",
                                         json={"current_value": 30},
                                         headers=auth_headers))
        assert body["data"]["achievement_pct"] == 30.0, (
            f"Expected 30.0%, got {body['data']['achievement_pct']}"
        )

    def test_achievement_pct_caps_at_100(self, client, auth_headers, goal_id):
        # _fmt() caps at min(cv/tv*100, 100), so 150/100 → 100%
        body = assert_success(client.put(f"/api/goals/{goal_id}",
                                         json={"current_value": 150},
                                         headers=auth_headers))
        assert body["data"]["achievement_pct"] == 100.0, (
            "achievement_pct should be capped at 100"
        )

    def test_goal_is_completed_when_target_met(self, client, auth_headers, goal_id):
        # goals.py sets is_completed=1 when cv >= tv
        body = assert_success(client.put(f"/api/goals/{goal_id}",
                                         json={"current_value": 100},
                                         headers=auth_headers))
        assert body["data"]["is_completed"] == 1, (
            "is_completed should be 1 when current_value >= target_value"
        )

    def test_update_goal_nothing_to_update_returns_422(self, client, auth_headers, goal_id):
        # goals.py: if not sets → 422 "Nothing to update."
        assert_error(client.put(f"/api/goals/{goal_id}", json={},
                                headers=auth_headers), 422)

    def test_update_goal_not_found_returns_404(self, client, auth_headers):
        assert_error(client.put(f"/api/goals/{NONEXISTENT_ID}",
                                json={"current_value": 10},
                                headers=auth_headers), 404)

    def test_goal_status_endpoint_returns_200(self, client, auth_headers, goal_id):
        body = assert_success(client.get(f"/api/goals/{goal_id}/status",
                                         headers=auth_headers))
        # goals.py adds remaining_kg to the status response
        assert "remaining_kg" in body["data"], (
            "Goal status response missing 'remaining_kg'"
        )

    def test_goal_status_remaining_kg_nonnegative(self, client, auth_headers, goal_id):
        body = assert_success(client.get(f"/api/goals/{goal_id}/status",
                                         headers=auth_headers))
        assert body["data"]["remaining_kg"] >= 0, "remaining_kg should not be negative"

    def test_goal_status_not_found_returns_404(self, client, auth_headers):
        assert_error(client.get(f"/api/goals/{NONEXISTENT_ID}/status",
                                headers=auth_headers), 404)

    def test_delete_goal_returns_200(self, client, auth_headers, goal_id):
        assert_success(client.delete(f"/api/goals/{goal_id}",
                                     headers=auth_headers))

    def test_deleted_goal_is_gone(self, client, auth_headers, goal_id):
        assert_error(client.get(f"/api/goals/{goal_id}", headers=auth_headers), 404)

    def test_delete_already_deleted_goal_returns_404(self, client, auth_headers, goal_id):
        assert_error(client.delete(f"/api/goals/{goal_id}", headers=auth_headers), 404)

    def test_delete_nonexistent_goal_returns_404(self, client, auth_headers):
        assert_error(client.delete(f"/api/goals/{NONEXISTENT_ID}",
                                   headers=auth_headers), 404)


# ── Tracking ──────────────────────────────────────────────────────────────────

class TestTracking:
    @pytest.fixture(scope="class")
    def record_id(self, client, auth_headers):
        r = client.post("/api/tracking/log", json={
            "trips": [{"mode": "bus", "km": 10}],
            "electricity_kwh": 5,
            "food_type": "vegetarian",
        }, headers=auth_headers)
        assert r.status_code == 201, (
            f"Failed to create fixture record: {r.get_data(as_text=True)}"
        )
        return r.get_json()["data"]["id"]

    def test_log_basic_record_returns_201(self, client, auth_headers):
        r = client.post("/api/tracking/log", json={
            "trips": [{"mode": "petrol_car", "km": 20}],
            "electricity_kwh": 10,
            "food_type": "non_veg",
        }, headers=auth_headers)
        assert r.status_code == 201

    def test_log_empty_body_returns_201(self, client, auth_headers):
        # tracking.py defaults all fields — empty body is valid
        assert client.post("/api/tracking/log", json={},
                           headers=auth_headers).status_code == 201

    def test_log_multiple_trips_returns_201(self, client, auth_headers):
        r = client.post("/api/tracking/log", json={
            "trips": [
                {"mode": "bus", "km": 5},
                {"mode": "train", "km": 20},
                {"mode": "petrol_car", "km": 10},
            ],
            "electricity_kwh": 8,
            "food_type": "vegetarian",
        }, headers=auth_headers)
        assert r.status_code == 201

    @pytest.mark.parametrize("mode", TRANSPORT_MODES)
    def test_log_each_transport_mode(self, client, auth_headers, mode):
        r = client.post("/api/tracking/log", json={
            "trips": [{"mode": mode, "km": 10}],
        }, headers=auth_headers)
        assert r.status_code == 201, f"Failed for transport mode '{mode}'"

    @pytest.mark.parametrize("food", FOOD_TYPES)
    def test_log_each_food_type(self, client, auth_headers, food):
        r = client.post("/api/tracking/log", json={
            "food_type": food, "electricity_kwh": 1,
        }, headers=auth_headers)
        assert r.status_code == 201, f"Failed for food_type '{food}'"

    def test_log_invalid_date_returns_422(self, client, auth_headers):
        # tracking.py validates date via date.fromisoformat
        r = client.post("/api/tracking/log", json={
            "date": "not-a-date",
        }, headers=auth_headers)
        assert_error(r, 422)

    def test_log_unauthenticated_returns_401(self, client):
        assert_error(client.post("/api/tracking/log",
                                 json={"electricity_kwh": 5}), 401)

    def test_log_response_has_emission_breakdown(self, client, auth_headers):
        r = client.post("/api/tracking/log", json={
            "trips": [{"mode": "petrol_car", "km": 20}],
            "electricity_kwh": 5,
        }, headers=auth_headers)
        data = r.get_json()["data"]
        for field in ("transport_emissions", "electricity_emissions",
                      "food_emissions", "fuel_emissions", "total_emissions"):
            assert field in data, f"Missing '{field}' in log response"

    def test_log_total_emissions_is_sum_of_parts(self, client, auth_headers):
        r = client.post("/api/tracking/log", json={
            "trips": [{"mode": "bus", "km": 10}],
            "electricity_kwh": 5,
            "food_type": "vegetarian",
        }, headers=auth_headers)
        d = r.get_json()["data"]
        expected = round(
            d["transport_emissions"] + d["electricity_emissions"] +
            d["food_emissions"] + d["fuel_emissions"], 4
        )
        assert abs(d["total_emissions"] - expected) < 0.01, (
            f"total_emissions {d['total_emissions']} ≠ sum of parts {expected}"
        )

    def test_get_records_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/tracking/records", headers=auth_headers))

    def test_get_records_has_items_total_page_fields(self, client, auth_headers):
        body = assert_success(client.get("/api/tracking/records", headers=auth_headers))
        d = body["data"]
        for key in ("items", "total", "page", "pages", "per_page"):
            assert key in d, f"Records response missing '{key}'"

    def test_get_records_items_is_list(self, client, auth_headers):
        body = assert_success(client.get("/api/tracking/records", headers=auth_headers))
        assert isinstance(body["data"]["items"], list), "'items' must be a list"

    def test_get_records_pagination_page_2(self, client, auth_headers):
        assert_success(client.get("/api/tracking/records?page=2", headers=auth_headers))

    def test_get_records_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/tracking/records"), 401)

    def test_get_single_record(self, client, auth_headers, record_id):
        body = assert_success(client.get(f"/api/tracking/records/{record_id}",
                                         headers=auth_headers))
        assert body["data"]["id"] == record_id

    def test_get_record_not_found_returns_404(self, client, auth_headers):
        assert_error(client.get(f"/api/tracking/records/{NONEXISTENT_ID}",
                                headers=auth_headers), 404)

    def test_update_record_electricity_emissions(self, client, auth_headers, record_id):
        body = assert_success(client.put(f"/api/tracking/records/{record_id}",
                                         json={"electricity_emissions": 2.5},
                                         headers=auth_headers))
        assert abs(body["data"]["electricity_emissions"] - 2.5) < 0.01

    def test_update_record_recalculates_total(self, client, auth_headers, record_id):
        body = assert_success(client.put(f"/api/tracking/records/{record_id}",
                                         json={"transport_emissions": 1.0,
                                               "electricity_emissions": 1.0},
                                         headers=auth_headers))
        d = body["data"]
        expected = round(
            d["transport_emissions"] + d["electricity_emissions"] +
            d["food_emissions"] + d["fuel_emissions"], 4
        )
        assert abs(d["total_emissions"] - expected) < 0.01, (
            "total_emissions not recalculated after update"
        )

    def test_update_record_empty_body_returns_422(self, client, auth_headers, record_id):
        # tracking.py: if not sets → 422 "Nothing to update."
        assert_error(client.put(f"/api/tracking/records/{record_id}",
                                json={}, headers=auth_headers), 422)

    def test_update_record_not_found_returns_404(self, client, auth_headers):
        assert_error(client.put(f"/api/tracking/records/{NONEXISTENT_ID}",
                                json={"transport_emissions": 1.0},
                                headers=auth_headers), 404)

    def test_delete_record_returns_200(self, client, auth_headers, record_id):
        assert_success(client.delete(f"/api/tracking/records/{record_id}",
                                     headers=auth_headers))

    def test_deleted_record_is_gone(self, client, auth_headers, record_id):
        assert_error(client.get(f"/api/tracking/records/{record_id}",
                                headers=auth_headers), 404)

    def test_delete_already_deleted_record_returns_404(self, client, auth_headers, record_id):
        assert_error(client.delete(f"/api/tracking/records/{record_id}",
                                   headers=auth_headers), 404)

    def test_delete_nonexistent_record_returns_404(self, client, auth_headers):
        assert_error(client.delete(f"/api/tracking/records/{NONEXISTENT_ID}",
                                   headers=auth_headers), 404)


# ── Dashboard ─────────────────────────────────────────────────────────────────

class TestDashboard:
    # analytics_service.get_analytics() returns:
    # daily, weekly, monthly, yearly, monthly_trend, category_breakdown,
    # sustainability_score

    def test_authenticated_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/dashboard/", headers=auth_headers))

    def test_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/dashboard/"), 401)

    def test_response_has_all_time_buckets(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        for key in ("daily", "weekly", "monthly", "yearly"):
            assert key in body["data"], f"Dashboard missing '{key}' bucket"

    def test_each_bucket_has_emission_fields(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        for bucket in ("daily", "weekly", "monthly"):
            d = body["data"][bucket]
            for field in ("total", "transport", "electricity", "food", "fuel", "records"):
                assert field in d, f"Bucket '{bucket}' missing field '{field}'"

    def test_has_monthly_trend_list(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        assert "monthly_trend" in body["data"], "Dashboard missing 'monthly_trend'"
        assert isinstance(body["data"]["monthly_trend"], list), (
            "'monthly_trend' should be a list"
        )

    def test_has_category_breakdown_list(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        assert "category_breakdown" in body["data"], "Dashboard missing 'category_breakdown'"
        assert isinstance(body["data"]["category_breakdown"], list)

    def test_has_sustainability_score(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        assert "sustainability_score" in body["data"], (
            "Dashboard missing 'sustainability_score'"
        )

    def test_sustainability_score_has_score_and_grade(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        sc = body["data"]["sustainability_score"]
        assert "score" in sc and "grade" in sc, (
            f"sustainability_score missing 'score' or 'grade': {sc}"
        )

    def test_sustainability_score_in_valid_range(self, client, auth_headers):
        body = assert_success(client.get("/api/dashboard/", headers=auth_headers))
        score = body["data"]["sustainability_score"]["score"]
        assert isinstance(score, (int, float)), "Score must be numeric"
        assert 0 <= score <= 100, f"Score {score} is outside 0–100 range"


# ── Leaderboard ───────────────────────────────────────────────────────────────

class TestLeaderboard:
    # leaderboard.py returns {"leaderboard": [...], "my_rank": {...}|None}

    def test_default_mode_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/leaderboard/", headers=auth_headers))

    def test_score_mode_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/leaderboard/?mode=score&limit=10",
                                  headers=auth_headers))

    def test_footprint_mode_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/leaderboard/?mode=footprint",
                                  headers=auth_headers))

    def test_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/leaderboard/"), 401)

    def test_response_has_leaderboard_and_my_rank(self, client, auth_headers):
        body = assert_success(client.get("/api/leaderboard/", headers=auth_headers))
        assert "leaderboard" in body["data"], "Missing 'leaderboard' key"
        assert "my_rank" in body["data"], "Missing 'my_rank' key"

    def test_leaderboard_is_list(self, client, auth_headers):
        body = assert_success(client.get("/api/leaderboard/", headers=auth_headers))
        assert isinstance(body["data"]["leaderboard"], list), (
            "'leaderboard' value should be a list"
        )

    def test_leaderboard_entries_have_required_fields(self, client, auth_headers):
        body = assert_success(client.get("/api/leaderboard/", headers=auth_headers))
        for entry in body["data"]["leaderboard"]:
            for field in ("user_id", "name", "score", "grade", "monthly_kg", "rank"):
                assert field in entry, f"Leaderboard entry missing '{field}': {entry}"

    def test_leaderboard_limit_respected(self, client, auth_headers):
        body = assert_success(client.get("/api/leaderboard/?limit=2",
                                         headers=auth_headers))
        assert len(body["data"]["leaderboard"]) <= 2, (
            "Returned more entries than requested limit"
        )

    def test_score_mode_sorted_descending(self, client, auth_headers):
        body = assert_success(client.get("/api/leaderboard/?mode=score",
                                         headers=auth_headers))
        entries = body["data"]["leaderboard"]
        if len(entries) > 1:
            scores = [e["score"] for e in entries]
            assert scores == sorted(scores, reverse=True), (
                "Score mode should be sorted in descending order"
            )

    def test_footprint_mode_sorted_ascending(self, client, auth_headers):
        body = assert_success(client.get("/api/leaderboard/?mode=footprint",
                                         headers=auth_headers))
        entries = body["data"]["leaderboard"]
        if len(entries) > 1:
            kgs = [e["monthly_kg"] for e in entries]
            assert kgs == sorted(kgs), (
                "Footprint mode should be sorted in ascending order (lower is better)"
            )


# ── Calculator ────────────────────────────────────────────────────────────────

class TestCalculator:
    # calculator.py returns the full EmissionCalculator.calculate_monthly() dict
    # plus trees_to_offset, global_avg_annual_kg, india_avg_annual_kg

    def test_petrol_car_calculation_returns_200(self, client, auth_headers):
        assert_success(client.post("/api/calculator/calculate", json={
            "trips": [{"mode": "petrol_car", "km": 30}],
            "electricity_kwh": 200,
            "food_type": "vegetarian",
        }, headers=auth_headers))

    def test_electric_car_calculation_returns_200(self, client, auth_headers):
        assert_success(client.post("/api/calculator/calculate", json={
            "trips": [{"mode": "electric_car", "km": 50}],
            "electricity_kwh": 100,
            "food_type": "vegan",
        }, headers=auth_headers))

    def test_empty_trips_returns_200(self, client, auth_headers):
        assert_success(client.post("/api/calculator/calculate", json={
            "trips": [], "electricity_kwh": 100, "food_type": "vegan",
        }, headers=auth_headers))

    def test_invalid_food_type_returns_422(self, client, auth_headers):
        # calculator.py: if food_type not in VALID_FOODS → 422
        assert_error(client.post("/api/calculator/calculate", json={
            "trips": [], "food_type": "invalid_diet",
        }, headers=auth_headers), 422)

    def test_unauthenticated_returns_401(self, client):
        assert_error(client.post("/api/calculator/calculate",
                                 json={"electricity_kwh": 100}), 401)

    def test_response_has_all_required_fields(self, client, auth_headers):
        body = assert_success(client.post("/api/calculator/calculate", json={
            "trips": [{"mode": "bus", "km": 10}],
            "electricity_kwh": 50,
            "food_type": "vegetarian",
        }, headers=auth_headers))
        d = body["data"]
        for field in ("transport_emissions", "electricity_emissions",
                      "food_emissions", "fuel_emissions",
                      "total_monthly_kg", "total_annual_kg", "total_annual_tonnes",
                      "breakdown_pct", "trees_to_offset",
                      "global_avg_annual_kg", "india_avg_annual_kg"):
            assert field in d, f"Calculator response missing '{field}'"

    def test_total_emissions_is_nonnegative(self, client, auth_headers):
        body = assert_success(client.post("/api/calculator/calculate", json={
            "trips": [], "electricity_kwh": 0,
        }, headers=auth_headers))
        assert body["data"]["total_monthly_kg"] >= 0, "total_monthly_kg should not be negative"

    def test_trees_to_offset_is_positive_int(self, client, auth_headers):
        body = assert_success(client.post("/api/calculator/calculate", json={
            "trips": [{"mode": "petrol_car", "km": 100}],
            "electricity_kwh": 200,
        }, headers=auth_headers))
        trees = body["data"]["trees_to_offset"]
        assert isinstance(trees, int) and trees >= 1, (
            f"trees_to_offset should be a positive integer, got {trees}"
        )

    def test_breakdown_pct_sums_near_100(self, client, auth_headers):
        body = assert_success(client.post("/api/calculator/calculate", json={
            "trips": [{"mode": "petrol_car", "km": 20}],
            "electricity_kwh": 50,
            "food_type": "vegetarian",
        }, headers=auth_headers))
        pct = body["data"]["breakdown_pct"]
        total = sum(pct.values())
        assert abs(total - 100.0) < 1.0, (
            f"breakdown_pct values should sum to ~100, got {total}"
        )

    def test_get_emission_factors_no_auth_required(self, client):
        # /api/calculator/factors is not protected
        r = client.get("/api/calculator/factors")
        assert r.status_code == 200
        body = r.get_json()
        for key in ("transport", "electricity", "fuel", "food"):
            assert key in body["data"], f"Emission factors missing '{key}'"

    def test_quick_calc_transport_returns_200(self, client, auth_headers):
        body = assert_success(client.post("/api/calculator/quick", json={
            "category": "transport", "mode": "bus", "value": 10,
        }, headers=auth_headers))
        assert "kg_co2e" in body["data"]

    def test_quick_calc_electricity_returns_200(self, client, auth_headers):
        body = assert_success(client.post("/api/calculator/quick", json={
            "category": "electricity", "value": 100,
        }, headers=auth_headers))
        assert "kg_co2e" in body["data"]

    def test_quick_calc_invalid_category_returns_422(self, client, auth_headers):
        assert_error(client.post("/api/calculator/quick", json={
            "category": "unknown", "value": 10,
        }, headers=auth_headers), 422)


# ── Recommendations ───────────────────────────────────────────────────────────

class TestRecommendations:
    # recommendations.py: POST / → generate + store; GET /history → last 10

    def test_post_returns_200(self, client, auth_headers):
        assert_success(client.post("/api/recommendations/", headers=auth_headers))

    def test_post_unauthenticated_returns_401(self, client):
        assert_error(client.post("/api/recommendations/"), 401)

    def test_response_has_tips_source_and_profile(self, client, auth_headers):
        body = assert_success(client.post("/api/recommendations/", headers=auth_headers))
        d = body["data"]
        assert "tips" in d, "Recommendations response missing 'tips'"
        assert "source" in d, "Recommendations response missing 'source'"
        assert "profile_snapshot" in d, "Recommendations response missing 'profile_snapshot'"

    def test_tips_is_nonempty_list(self, client, auth_headers):
        body = assert_success(client.post("/api/recommendations/", headers=auth_headers))
        tips = body["data"]["tips"]
        assert isinstance(tips, list) and len(tips) > 0, (
            f"'tips' should be a non-empty list, got: {tips}"
        )

    def test_each_tip_is_nonempty_string(self, client, auth_headers):
        body = assert_success(client.post("/api/recommendations/", headers=auth_headers))
        for tip in body["data"]["tips"]:
            assert isinstance(tip, str) and len(tip) > 0, (
                f"Each tip should be a non-empty string, got: {tip!r}"
            )

    def test_source_is_valid_value(self, client, auth_headers):
        body = assert_success(client.post("/api/recommendations/", headers=auth_headers))
        assert body["data"]["source"] in ("rule_engine", "gemini_ai"), (
            f"Unexpected source: {body['data']['source']}"
        )

    def test_history_returns_list(self, client, auth_headers):
        body = assert_success(client.get("/api/recommendations/history",
                                         headers=auth_headers))
        assert isinstance(body["data"], list), "'history' data should be a list"

    def test_history_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/recommendations/history"), 401)

    def test_history_grows_after_new_recommendation(self, client, auth_headers):
        before = len(assert_success(
            client.get("/api/recommendations/history", headers=auth_headers)
        )["data"])
        client.post("/api/recommendations/", headers=auth_headers)
        after = len(assert_success(
            client.get("/api/recommendations/history", headers=auth_headers)
        )["data"])
        assert after > before, "History count should increase after generating a new recommendation"


# ── Prediction ────────────────────────────────────────────────────────────────

class TestPrediction:
    # prediction_service.predict_12_months() returns:
    # trend, slope_per_week, months, predictions_kg,
    # annual_forecast, annual_forecast_tonnes
    # OR a "need at least 7 days of data" message dict

    def test_authenticated_returns_200(self, client, auth_headers):
        assert_success(client.get("/api/prediction/", headers=auth_headers))

    def test_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/prediction/"), 401)

    def test_response_data_is_dict(self, client, auth_headers):
        body = assert_success(client.get("/api/prediction/", headers=auth_headers))
        assert isinstance(body["data"], dict), (
            f"Prediction data should be a dict, got {type(body['data'])}"
        )

    def test_response_has_months_and_predictions(self, client, auth_headers):
        body = assert_success(client.get("/api/prediction/", headers=auth_headers))
        d = body["data"]
        # Both full predictions and the "need more data" stub include these keys
        assert "months" in d, "Prediction response missing 'months'"
        assert "predictions_kg" in d, "Prediction response missing 'predictions_kg'"
        assert "annual_forecast" in d, "Prediction response missing 'annual_forecast'"

    def test_months_and_predictions_same_length(self, client, auth_headers):
        body = assert_success(client.get("/api/prediction/", headers=auth_headers))
        d = body["data"]
        assert len(d["months"]) == len(d["predictions_kg"]), (
            "months and predictions_kg arrays must be the same length"
        )

    def test_annual_forecast_is_nonnegative(self, client, auth_headers):
        body = assert_success(client.get("/api/prediction/", headers=auth_headers))
        assert body["data"]["annual_forecast"] >= 0, (
            "annual_forecast should not be negative"
        )


# ── Reports ───────────────────────────────────────────────────────────────────

class TestReports:
    def test_csv_export_authenticated(self, client, auth_headers):
        r = client.get("/api/reports/csv", headers=auth_headers)
        assert r.status_code == 200
        assert "text/csv" in r.content_type, (
            f"Expected CSV content-type, got: {r.content_type}"
        )

    def test_csv_export_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/reports/csv"), 401)

    def test_csv_export_has_header_row(self, client, auth_headers):
        r = client.get("/api/reports/csv", headers=auth_headers)
        content = r.get_data(as_text=True)
        assert "Date" in content and "Total" in content, (
            "CSV should include a header row with 'Date' and 'Total'"
        )

    def test_csv_custom_days_param(self, client, auth_headers):
        r = client.get("/api/reports/csv?days=7", headers=auth_headers)
        assert r.status_code == 200

    def test_summary_report_authenticated(self, client, auth_headers):
        # /api/reports/summary returns get_analytics() — same shape as dashboard
        body = assert_success(client.get("/api/reports/summary", headers=auth_headers))
        assert "monthly" in body["data"], "Summary report missing 'monthly' key"

    def test_summary_report_unauthenticated_returns_401(self, client):
        assert_error(client.get("/api/reports/summary"), 401)


# ── Offset Calculator ─────────────────────────────────────────────────────────

class TestOffset:
    # offset.py: POST /api/offset/
    # Requires annual_kg OR annual_tonnes (non-zero). Returns trees_required, area_m2, etc.

    def test_offset_by_annual_kg_returns_200(self, client, auth_headers):
        body = assert_success(client.post("/api/offset/", json={
            "annual_kg": 2000,
        }, headers=auth_headers))
        for field in ("trees_required", "area_m2", "area_hectares",
                      "kg_per_tree_year", "offset_options"):
            assert field in body["data"], f"Offset response missing '{field}'"

    def test_offset_by_annual_tonnes_returns_200(self, client, auth_headers):
        body = assert_success(client.post("/api/offset/", json={
            "annual_tonnes": 2.0,
        }, headers=auth_headers))
        # annual_tonnes * 1000 → annual_kg → trees
        assert body["data"]["trees_required"] >= 1

    def test_offset_no_input_returns_422(self, client, auth_headers):
        # offset.py: if kg==0 and t==0 → 422
        assert_error(client.post("/api/offset/", json={},
                                 headers=auth_headers), 422)

    def test_offset_unauthenticated_returns_401(self, client):
        assert_error(client.post("/api/offset/", json={"annual_kg": 1000}), 401)

    def test_offset_trees_required_is_positive(self, client, auth_headers):
        body = assert_success(client.post("/api/offset/", json={
            "annual_kg": 500,
        }, headers=auth_headers))
        assert body["data"]["trees_required"] >= 1, (
            "trees_required must be at least 1 (EmissionCalculator.trees_to_offset uses max(1, ...))"
        )

    def test_offset_options_has_three_methods(self, client, auth_headers):
        body = assert_success(client.post("/api/offset/", json={
            "annual_kg": 1000,
        }, headers=auth_headers))
        options = body["data"]["offset_options"]
        assert len(options) == 3, (
            f"Expected 3 offset options, got {len(options)}"
        )
        methods = {o["method"] for o in options}
        assert "Plant trees" in methods, "Expected 'Plant trees' option"
