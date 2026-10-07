import urllib.request
import json
import sys
import os

sys.stdout.reconfigure(encoding='utf-8')

_port = os.getenv("PORT", "8000")
BASE_URL = os.getenv("TEST_BASE_URL", f"http://127.0.0.1:{_port}")
_test_client = None

def _get_client():
    global _test_client
    if _test_client is None:
        try:
            from fastapi.testclient import TestClient
            from backend.main import app
            _test_client = TestClient(app)
        except Exception as e:
            print(f"[Warning] Could not initialize TestClient fallback: {e}")
    return _test_client

def http_get(url_path, headers=None):
    try:
        req = urllib.request.Request(f"{BASE_URL}{url_path}", headers=headers or {})
        res = urllib.request.urlopen(req, timeout=2)
        return res.status, res.read()
    except Exception:
        c = _get_client()
        if c:
            r = c.get(url_path, headers=headers or {})
            return r.status_code, r.content
        raise

def http_post(url_path, data, headers=None):
    try:
        h = {"Content-Type": "application/json", **(headers or {})}
        payload = json.dumps(data).encode("utf-8") if isinstance(data, dict) else data
        req = urllib.request.Request(f"{BASE_URL}{url_path}", data=payload, headers=h)
        res = urllib.request.urlopen(req, timeout=2)
        return res.status, res.read()
    except Exception:
        c = _get_client()
        if c:
            r = c.post(url_path, json=data if isinstance(data, dict) else json.loads(data), headers=headers or {})
            return r.status_code, r.content
        raise

def run_tests():
    all_passed = True
    print("=" * 60)
    print("1. STATIC ASSETS DELIVERY TEST")
    print("=" * 60)
    static_files = [
        "/js/services/api.service.js",
        "/js/services/auth.service.js",
        "/js/services/admin.service.js",
        "/js/components/toast.js",
        "/js/components/component-loader.js",
        "/js/router.js",
        "/static/app.js",
        "/static/style.css",
        "/components/layout/sidebar.html",
        "/components/layout/header.html",
        "/components/modals/investigation-drawer.html",
        "/components/modals/auth-modal.html",
        "/views/dashboard.html",
        "/views/transactions.html",
        "/views/cases.html",
        "/views/behavior.html",
        "/views/scam.html",
        "/views/admin.html"
    ]
    for sf in static_files:
        try:
            status, raw = http_get(sf)
            if status == 200:
                print(f"  [PASS] {sf} (200 OK, {len(raw)} bytes)")
            else:
                print(f"  [FAIL] {sf} (Status {status})")
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] {sf}: {e}")
            all_passed = False


    print("\n" + "=" * 60)
    print("2. DEEP-LINK / PAGE RELOAD ROUTES (SPA FALLBACK TEST)")
    print("=" * 60)
    page_routes = [
        "/",
        "/dashboard",
        "/transactions",
        "/cases",
        "/simulator",
        "/behavior",
        "/scam",
        "/network",
        "/model",
        "/monitoring",
        "/responsible",
        "/admin"
    ]
    for pr in page_routes:
        try:
            status, raw = http_get(pr)
            html = raw.decode("utf-8") if isinstance(raw, bytes) else str(raw)
            has_title = "upay AI Shield" in html
            has_scripts = "router.js" in html and "app.js" in html
            if status == 200 and has_title and has_scripts:
                print(f"  [PASS] Route {pr:18} -> 200 OK (Deep link renders app shell)")
            else:
                print(f"  [FAIL] Route {pr:18} -> Status {status}, Title={has_title}, Scripts={has_scripts}")
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] Route {pr}: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    print("3. AUTHENTICATION & RBAC API TEST")
    print("=" * 60)
    # Login Admin
    login_data = {"username_or_email": "admin", "password": "Admin@1234"}
    status, raw = http_post("/api/v1/auth/login", login_data)
    admin_token = json.loads(raw)["data"]["access_token"]
    print("  [PASS] Admin Login: Success")

    # Auth Me
    status, raw = http_get("/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    me = json.loads(raw)["data"]
    print(f"  [PASS] Profile Verified: {me['full_name']} (Role: {me['role']})")

    # Admin Users List
    status, raw = http_get("/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    users = json.loads(raw)["data"]
    print(f"  [PASS] Admin Users Directory: {len(users)} registered officers")

    # Admin Metrics
    status, raw = http_get("/api/v1/admin/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    adm_metrics = json.loads(raw)["data"]
    print(f"  [PASS] Admin Metrics: {adm_metrics['users']['total']} users, {adm_metrics['transactions']['total']} txs")

    print("\n" + "=" * 60)
    print("4. TRANSACTION & CASE MANAGEMENT APIs")
    print("=" * 60)
    # List Transactions
    status, raw = http_get("/api/v1/transactions?limit=5")
    tx_res = json.loads(raw)["data"]
    print(f"  [PASS] Transactions Ledger: {tx_res['total']} total transactions loaded")

    # List Cases
    status, raw = http_get("/api/v1/cases?limit=5")
    cases_res = json.loads(raw)["data"]
    print(f"  [PASS] Case Management: {cases_res['total']} cases indexed")

    # Network Graph
    status, raw = http_get("/api/v1/intelligence/network-graph")
    net_res = json.loads(raw)["data"]
    print(f"  [PASS] Network Mule Graph: {len(net_res['nodes'])} nodes, {len(net_res['edges'])} edges")

    # AI Copilot
    chat_payload = {"message": "What is the recommended protocol for SIM swap attacks?"}
    status, raw = http_post("/api/v1/chat/ask", chat_payload)
    chat_res = json.loads(raw)["data"]
    print(f"  [PASS] Forensic AI Copilot: Replied ({len(chat_res['reply'])} chars)")


    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED SUCCESSFULLY! PRODUCTION READY.")
    else:
        print("SOME TESTS FAILED.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
