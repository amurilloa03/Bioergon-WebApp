import requests

# Simulation script to check form deletion backend
BASE_URL = "http://127.0.0.1:5000"

def test_delete():
    # 1. Login as Pepe (admin)
    session = requests.Session()
    login_data = {
        "user": "Pepe",
        "password": "12345"
    }
    # Note: Login might require CSRF token even for the login form if CSRFProtect(app) is global
    # Let's check if the login form in index.html has a CSRF token
    
    # First, get the login page to grab CSRF if it's there
    r = session.get(BASE_URL + "/")
    # simple regex to find csrf if present
    import re
    token_match = re.search(r'name="csrf_token" value="([^"]+)"', r.text)
    if token_match:
        login_data["csrf_token"] = token_match.group(1)
        print(f"Found CSRF token for login: {login_data['csrf_token'][:10]}...")

    res = session.post(BASE_URL + "/login", data=login_data)
    if res.status_code == 200 and "/formularios" in res.url:
        print("Login successful.")
    else:
        print(f"Login failed. Status: {res.status_code}, URL: {res.url}")
        return

    # 2. Get the forms list and extract a form ID
    res = session.get(BASE_URL + "/formularios")
    # find action="/formularios/(\d+)/delete"
    form_matches = re.findall(r'action="/formularios/(\d+)/delete"', res.text)
    if not form_matches:
        print("No forms found to delete.")
        return
    
    form_id = form_matches[0]
    print(f"Attempting to delete form {form_id}...")

    # Grab CSRF token from the forms page
    token_match = re.search(r'name="csrf_token" value="([^"]+)"', res.text)
    if not token_match:
        print("Could not find CSRF token on forms page.")
        return
    
    delete_data = {
        "csrf_token": token_match.group(1)
    }

    # 3. Send POST to delete
    res = session.post(BASE_URL + f"/formularios/{form_id}/delete", data=delete_data, allow_redirects=False)
    
    print(f"Delete Response Status: {res.status_code}")
    if res.status_code == 302:
        print(f"Redirected to: {res.headers.get('Location')}")
    else:
        print("Response Body Snippet:")
        print(res.text[:500])

if __name__ == "__main__":
    test_delete()
