# NetLoom Client API Documentation

Documentation for connecting managed WireGuard peers to the NetLoom Client API.

---

## Endpoints

| Protocol | Port | Base URL |
|----------|------|----------|
| HTTP | 7771 | `http://<server>:7771/api/v1/client/` |
| HTTPS | 7772 | `https://<server>:7772/api/v1/client/` |

**Recommended:** Use HTTPS (port 7772) for all production connections.

---

## How It Works

The client API uses **auto-provisioning**: on first login, NetLoom automatically creates a WireGuard peer for the user, named `<username>-<os>` based on the detected operating system from the `User-Agent` header. No manual admin setup is required.

| OS detected | Peer name example |
|---|---|
| Windows | `admin-windows` |
| macOS | `admin-macos` |
| Linux | `admin-linux` |
| Android | `admin-android` |
| iOS | `admin-ios` |
| Unknown | `admin-unknown` |

**Client flow:**
1. `POST /login` → receive `access_token` + `device_id`
2. `GET /config` → receive full WireGuard configuration (no peer_id needed)
3. Configure WireGuard interface using the returned keys and allowed IPs
4. `POST /status` → report heartbeat while connected

---

## Authentication

### Login

```http
POST /api/v1/client/login
Content-Type: application/json
User-Agent: MyApp/1.0 (Windows NT 10.0)

{
  "username": "admin",
  "password": "sode1450"
}
```

**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "BYVaqMI4ETPNncMgbVQM-m8JAK_GAJy6Ne2TeLDOhQ1z...",
  "token_type": "bearer",
  "expires_in": 3600,
  "device_id": 1,
  "requires_registration": false
}
```

- `device_id`: ID of the auto-provisioned (or existing) device for this user
- `requires_registration`: always `false` — peer is created automatically on first login

### Using the Token

Include the `access_token` in all subsequent requests:

```http
GET /api/v1/client/config
Authorization: Bearer <access_token>
```

---

## API Endpoints

### Get Full Configuration

```http
GET /api/v1/client/config
Authorization: Bearer <token>
```

Returns the complete WireGuard configuration for the authenticated user's peer. The peer is inferred from the token — no `peer_id` parameter needed.

**Response (200 OK):**
```json
{
  "revision": 5,
  "server": {
    "public_key": "sH7S/VDO3orhmBaHTN7dnu7Y4E1ayAd0SmNbJkXqu0k=",
    "endpoint": "vpn.example.com",
    "listen_port": 51888
  },
  "interface": {
    "tunnel_address": "100.79.0.6/32",
    "allowed_ips": ["10.1.1.0/24", "192.168.70.0/23"],
    "dns": null
  },
  "peer": {
    "private_key": "6GYtYclKjSaSANzr9LclL0QGcojCEXlOYIm6PoYAbUU=",
    "address": "100.79.0.6/32",
    "dns": null,
    "persistent_keepalive": 25
  },
  "metadata": {
    "peer_id": 6,
    "peer_name": "admin-windows",
    "peer_type": "roadwarrior",
    "device_id": 1,
    "device_name": "admin-windows",
    "os_type": "windows",
    "generated_at": "2026-04-02T14:06:55.779536+00:00"
  }
}
```

### Get Config Version

```http
GET /api/v1/client/config/version
Authorization: Bearer <token>
```

Returns the current configuration revision. Use this to poll for changes without fetching the full config.

**Response (200 OK):**
```json
{
  "current_revision": 5,
  "last_updated_at": "2026-04-02T13:00:00Z"
}
```

### Get Delta Configuration

```http
GET /api/v1/client/config/delta?client_revision=<revision>
Authorization: Bearer <token>
```

Returns whether there are configuration changes since the client's last known revision.

| Parameter | Type | Description |
|---|---|---|
| `client_revision` | int | Last revision the client applied (default: `0`) |

**Response (200 OK):**
```json
{
  "current_revision": 5,
  "client_revision": 3,
  "has_changes": true,
  "changes": []
}
```

### Report Status

```http
POST /api/v1/client/status
Authorization: Bearer <token>
Content-Type: application/json

{
  "device_id": 1,
  "tunnel_status": "connected",
  "bytes_sent": 1048576,
  "bytes_received": 2097152
}
```

Reports the device heartbeat and tunnel state. The `device_id` must belong to the authenticated user.

**Response (200 OK):**
```json
{
  "status": "ok",
  "timestamp": "2026-04-02T14:30:00Z"
}
```

---

## TLS Certificate

The server uses a self-signed certificate. You have two options:

### Option 1: Skip Verification (Development)

```python
import requests

response = requests.post(
    "https://192.168.70.165:7772/api/v1/client/login",
    json={"username": "admin", "password": "sode1450"},
    verify=False
)
```

```bash
curl -k https://192.168.70.165:7772/api/v1/client/login \
  -X POST \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"sode1450"}'
```

### Option 2: Pin Certificate (Production)

Download the certificate from the server:
```bash
openssl s_client -connect <server>:7772 -servername netloom.local </dev/null 2>/dev/null | openssl x509 -out netloom.crt
```

Use it in your client:
```python
import requests

response = requests.post(
    "https://192.168.70.165:7772/api/v1/client/login",
    json={"username": "admin", "password": "sode1450"},
    verify="/path/to/netloom.crt"
)
```

**Certificate fingerprint (SHA1):**
```
D5:7A:B5:8E:36:AA:02:3C:80:5D:12:72:68:36:C7:14:1C:A1:D7:07
```

Verify the fingerprint matches before trusting the certificate:
```bash
openssl x509 -in netloom.crt -noout -fingerprint -sha1
```

---

## Code Examples

### Python

```python
import requests
from typing import Optional

class NetLoomClient:
    def __init__(self, base_url: str, verify: bool | str = False):
        self.base_url = base_url.rstrip("/")
        self.verify = verify
        self.access_token: Optional[str] = None
        self.device_id: Optional[int] = None

    def login(self, username: str, password: str) -> dict:
        """
        Authenticate and store access token.
        On first login, NetLoom auto-creates a WireGuard peer for this user.
        """
        response = requests.post(
            f"{self.base_url}/api/v1/client/login",
            json={"username": username, "password": password},
            headers={"User-Agent": "MyApp/1.0 (Windows NT 10.0)"},
            verify=self.verify,
        )
        response.raise_for_status()
        data = response.json()
        self.access_token = data["access_token"]
        self.device_id = data["device_id"]
        return data

    def _auth_headers(self) -> dict:
        return {"Authorization": f"Bearer {self.access_token}"}

    def get_config(self) -> dict:
        """Get full WireGuard configuration. Peer is inferred from the token."""
        response = requests.get(
            f"{self.base_url}/api/v1/client/config",
            headers=self._auth_headers(),
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()

    def get_version(self) -> dict:
        """Get current config revision (cheap poll for changes)."""
        response = requests.get(
            f"{self.base_url}/api/v1/client/config/version",
            headers=self._auth_headers(),
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()

    def get_delta(self, client_revision: int = 0) -> dict:
        """Check for configuration changes since client_revision."""
        response = requests.get(
            f"{self.base_url}/api/v1/client/config/delta",
            params={"client_revision": client_revision},
            headers=self._auth_headers(),
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()

    def report_status(self, tunnel_status: str, bytes_sent: int = 0, bytes_received: int = 0) -> dict:
        """Report tunnel heartbeat."""
        response = requests.post(
            f"{self.base_url}/api/v1/client/status",
            json={
                "device_id": self.device_id,
                "tunnel_status": tunnel_status,
                "bytes_sent": bytes_sent,
                "bytes_received": bytes_received,
            },
            headers=self._auth_headers(),
            verify=self.verify,
        )
        response.raise_for_status()
        return response.json()


# Usage
client = NetLoomClient(
    base_url="https://192.168.70.165:7772",
    verify=False,  # Or path to certificate file
)

login_data = client.login("admin", "sode1450")
print(f"Device ID: {login_data['device_id']}")  # auto-provisioned

config = client.get_config()
print(f"Tunnel IP: {config['interface']['tunnel_address']}")
print(f"Private key: {config['peer']['private_key']}")
```

### cURL

```bash
# Login — peer is auto-created on first call
TOKEN=$(curl -sk https://192.168.70.165:7772/api/v1/client/login \
  -X POST \
  -H "Content-Type: application/json" \
  -H "User-Agent: MyApp/1.0 (Windows NT 10.0)" \
  -d '{"username":"admin","password":"sode1450"}' | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

# Get full config (no peer_id needed)
curl -sk https://192.168.70.165:7772/api/v1/client/config \
  -H "Authorization: Bearer $TOKEN"

# Poll for changes
curl -sk "https://192.168.70.165:7772/api/v1/client/config/delta?client_revision=3" \
  -H "Authorization: Bearer $TOKEN"

# Report heartbeat
curl -sk https://192.168.70.165:7772/api/v1/client/status \
  -X POST \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"device_id":1,"tunnel_status":"connected","bytes_sent":1048576,"bytes_received":2097152}'
```

### Go

```go
package main

import (
    "bytes"
    "crypto/tls"
    "encoding/json"
    "fmt"
    "net/http"
)

type NetLoomClient struct {
    BaseURL     string
    AccessToken string
    DeviceID    int
    HTTPClient  *http.Client
}

func NewNetLoomClient(baseURL string, insecure bool) *NetLoomClient {
    tr := &http.Transport{
        TLSClientConfig: &tls.Config{InsecureSkipVerify: insecure},
    }
    return &NetLoomClient{
        BaseURL:    baseURL,
        HTTPClient: &http.Client{Transport: tr},
    }
}

func (c *NetLoomClient) Login(username, password string) error {
    body, _ := json.Marshal(map[string]string{"username": username, "password": password})
    req, _ := http.NewRequest("POST", c.BaseURL+"/api/v1/client/login", bytes.NewBuffer(body))
    req.Header.Set("Content-Type", "application/json")
    req.Header.Set("User-Agent", "MyApp/1.0 (Windows NT 10.0)")

    resp, err := c.HTTPClient.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()

    var data struct {
        AccessToken string `json:"access_token"`
        DeviceID    int    `json:"device_id"`
    }
    json.NewDecoder(resp.Body).Decode(&data)
    c.AccessToken = data.AccessToken
    c.DeviceID = data.DeviceID
    return nil
}

func (c *NetLoomClient) GetConfig() (map[string]interface{}, error) {
    req, _ := http.NewRequest("GET", c.BaseURL+"/api/v1/client/config", nil)
    req.Header.Set("Authorization", "Bearer "+c.AccessToken)

    resp, err := c.HTTPClient.Do(req)
    if err != nil {
        return nil, err
    }
    defer resp.Body.Close()

    var config map[string]interface{}
    json.NewDecoder(resp.Body).Decode(&config)
    return config, nil
}

func main() {
    client := NewNetLoomClient("https://192.168.70.165:7772", true)

    if err := client.Login("admin", "sode1450"); err != nil {
        panic(err)
    }
    fmt.Printf("Device ID: %d\n", client.DeviceID)

    config, err := client.GetConfig()
    if err != nil {
        panic(err)
    }
    fmt.Printf("Config: %+v\n", config)
}
```

---

## Error Responses

| HTTP Code | Meaning |
|-----------|---------|
| 200 | Success |
| 400 | Bad Request (missing parameters) |
| 401 | Unauthorized (invalid credentials or expired token) |
| 403 | Forbidden |
| 404 | Not Found |
| 500 | Internal Server Error |

**Example error:**
```json
{
  "detail": "Invalid credentials"
}
```

---

## Security Notes

1. **Always use HTTPS** (port 7772) in production to encrypt traffic
2. **Pin the certificate** or verify the SHA1 fingerprint before trusting the connection
3. **Store tokens securely** — access tokens expire after 1 hour
4. **Use refresh tokens** to obtain new access tokens without re-authenticating
5. **Restrict API access** to trusted networks using firewall rules
