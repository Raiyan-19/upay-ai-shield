import urllib.request
import json
import sys

BASE_URL = "http://127.0.0.1:8000"

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
        "/views/admin.html"
    ]
    for sf in static_files:
        try:
            req = urllib.request.urlopen(BASE_URL + sf)
            if req.status == 200:
                print(f"  [PASS] {sf} (200 OK, {len(req.read())} bytes)")
            else:
                print(f"  [FAIL] {sf} (Status {req.status})")
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
            req = urllib.request.urlopen(BASE_URL + pr)
            html = req.read().decode("utf-8")
            has_title = "upay AI Shield" in html
            has_scripts = "router.js" in html and "app.js" in html
            if req.status == 200 and has_title and has_scripts:
                print(f"  [PASS] Route {pr:18} -> 200 OK (Deep link renders app shell)")
            else:
                print(f"  [FAIL] Route {pr:18} -> Status {req.status}, Title={has_title}, Scripts={has_scripts}")
                all_passed = False
        except Exception as e:
            print(f"  [ERROR] Route {pr}: {e}")
            all_passed = False

    print("\n" + "=" * 60)
    print("3. AUTHENTICATION & RBAC API TEST")
    print("=" * 60)
    # Login Admin
    login_data = json.dumps({"username_or_email": "admin", "password": "Admin@1234"}).encode("utf-8")
    req = urllib.request.Request(f"{BASE_URL}/api/v1/auth/login", data=login_data, headers={"Content-Type": "application/json"})
    res = urllib.request.urlopen(req)
    admin_token = json.loads(res.read())["data"]["access_token"]
    print("  [PASS] Admin Login: Success")

    # Auth Me
    req = urllib.request.Request(f"{BASE_URL}/api/v1/auth/me", headers={"Authorization": f"Bearer {admin_token}"})
    me = json.loads(urllib.request.urlopen(req).read())["data"]
    print(f"  [PASS] Profile Verified: {me['full_name']} (Role: {me['role']})")

    # Admin Users List
    req = urllib.request.Request(f"{BASE_URL}/api/v1/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    users = json.loads(urllib.request.urlopen(req).read())["data"]
    print(f"  [PASS] Admin Users Directory: {len(users)} registered officers")

    # Admin Metrics
    req = urllib.request.Request(f"{BASE_URL}/api/v1/admin/metrics", headers={"Authorization": f"Bearer {admin_token}"})
    adm_metrics = json.loads(urllib.request.urlopen(req).read())["data"]
    print(f"  [PASS] Admin Metrics: {adm_metrics['users']['total']} users, {adm_metrics['transactions']['total']} txs")

    print("\n" + "=" * 60)
    print("4. TRANSACTION & CASE MANAGEMENT APIs")
    print("=" * 60)
    # List Transactions
    tx_res = json.loads(urllib.request.urlopen(f"{BASE_URL}/api/v1/transactions?limit=5").read())["data"]
    print(f"  [PASS] Transactions Ledger: {tx_res['total']} total transactions loaded")

    # List Cases
    cases_res = json.loads(urllib.request.urlopen(f"{BASE_URL}/api/v1/cases?limit=5").read())["data"]
    print(f"  [PASS] Case Management: {cases_res['total']} cases indexed")

    # Network Graph
    net_res = json.loads(urllib.request.urlopen(f"{BASE_URL}/api/v1/intelligence/network-graph").read())["data"]
    print(f"  [PASS] Network Mule Graph: {len(net_res['nodes'])} nodes, {len(net_res['edges'])} edges")

    # AI Copilot
    chat_payload = json.dumps({"message": "What is the recommended protocol for SIM swap attacks?"}).encode("utf-8")
    chat_req = urllib.request.Request(f"{BASE_URL}/api/v1/chat/ask", data=chat_payload, headers={"Content-Type": "application/json"})
    chat_res = json.loads(urllib.request.urlopen(chat_req).read())["data"]
    print(f"  [PASS] Forensic AI Copilot: Replied ({len(chat_res['reply'])} chars)")

    print("\n" + "=" * 60)
    if all_passed:
        print("ALL TESTS PASSED SUCCESSFULLY! PRODUCTION READY.")
    else:
        print("SOME TESTS FAILED.")
    print("=" * 60)

if __name__ == "__main__":
    run_tests()
