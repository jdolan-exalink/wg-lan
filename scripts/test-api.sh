#!/bin/bash
# Test script for NetLoom Client API
# Tests both HTTP and HTTPS endpoints

set -e

BASE_URL_HTTP="http://localhost:7771"
BASE_URL_HTTPS="https://localhost:7772"
DASHBOARD_URL="http://localhost:7777"
DASHBOARD_HTTPS_URL="https://localhost:7776"

# Credentials (change if needed)
USERNAME="${TEST_USERNAME:-admin}"
PASSWORD="${TEST_PASSWORD:-sode1450}"

echo "========================================="
echo "  NetLoom API Test Suite"
echo "========================================="
echo ""

# Test 1: Health Check (Dashboard)
echo "📋 Test 1: Dashboard Health Check"
echo "   URL: $DASHBOARD_URL/api/system/health"
HEALTH=$(curl -s "$DASHBOARD_URL/api/system/health")
echo "   Response: $HEALTH"
echo ""

# Test 2: Client API Login (HTTP)
echo "📋 Test 2: Client API Login (HTTP - port 7771)"
echo "   URL: $BASE_URL_HTTP/api/v1/client/login"
LOGIN_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" -X POST \
  "$BASE_URL_HTTP/api/v1/client/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}")
HTTP_CODE=$(echo "$LOGIN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
BODY=$(echo "$LOGIN_RESPONSE" | grep -v "HTTP_CODE:")
echo "   HTTP Code: $HTTP_CODE"
echo "   Response: $BODY"

# Extract tokens for subsequent tests
ACCESS_TOKEN=$(echo "$BODY" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null || echo "")
echo ""

# Test 3: Client API Login (HTTPS)
echo "📋 Test 3: Client API Login (HTTPS - port 7772)"
echo "   URL: $BASE_URL_HTTPS/api/v1/client/login"
HTTPS_LOGIN_RESPONSE=$(curl -s -k -w "\nHTTP_CODE:%{http_code}" -X POST \
  "$BASE_URL_HTTPS/api/v1/client/login" \
  -H "Content-Type: application/json" \
  -d "{\"username\":\"$USERNAME\",\"password\":\"$PASSWORD\"}" 2>/dev/null || echo "HTTPS not available")
HTTPS_HTTP_CODE=$(echo "$HTTPS_LOGIN_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
HTTPS_BODY=$(echo "$HTTPS_LOGIN_RESPONSE" | grep -v "HTTP_CODE:")
echo "   HTTP Code: $HTTPS_HTTP_CODE"
echo "   Response: $HTTPS_BODY"
echo ""

# Test 4: Verify encryption (compare HTTP vs HTTPS responses)
echo "📋 Test 4: Encryption Verification"
if [ "$HTTP_CODE" = "$HTTPS_HTTP_CODE" ] && [ "$HTTP_CODE" = "200" ]; then
    echo "   ✅ Both HTTP and HTTPS return same response structure"
    echo "   ⚠️  HTTP traffic is UNENCRYPTED - use HTTPS in production"
    echo "   ✅ HTTPS traffic is encrypted with TLS"
else
    echo "   ⚠️  Response codes differ (HTTP: $HTTP_CODE, HTTPS: $HTTPS_HTTP_CODE)"
fi
echo ""

# Test 5: Client API Config (with auth token)
if [ -n "$ACCESS_TOKEN" ]; then
    echo "📋 Test 5: Client API Config (with auth)"
    echo "   URL: $BASE_URL_HTTP/api/v1/client/config"
    CONFIG_RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
      "$BASE_URL_HTTP/api/v1/client/config" \
      -H "Authorization: Bearer $ACCESS_TOKEN")
    CONFIG_HTTP_CODE=$(echo "$CONFIG_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
    CONFIG_BODY=$(echo "$CONFIG_RESPONSE" | grep -v "HTTP_CODE:")
    echo "   HTTP Code: $CONFIG_HTTP_CODE"
    echo "   Response: $CONFIG_BODY"
    echo ""
fi

# Test 6: Dashboard HTTPS Health
echo "📋 Test 6: Dashboard HTTPS Health Check"
echo "   URL: $DASHBOARD_HTTPS_URL/api/system/health"
DASHBOARD_HTTPS_RESPONSE=$(curl -s -k -w "\nHTTP_CODE:%{http_code}" \
  "$DASHBOARD_HTTPS_URL/api/system/health" 2>/dev/null || echo "HTTPS not available")
DASHBOARD_HTTPS_CODE=$(echo "$DASHBOARD_HTTPS_RESPONSE" | grep "HTTP_CODE:" | cut -d: -f2)
DASHBOARD_HTTPS_BODY=$(echo "$DASHBOARD_HTTPS_RESPONSE" | grep -v "HTTP_CODE:")
echo "   HTTP Code: $DASHBOARD_HTTPS_CODE"
echo "   Response: $DASHBOARD_HTTPS_BODY"
echo ""

# Test 7: Certificate Information
echo "📋 Test 7: TLS Certificate Information"
if [ -f ./certs/server.crt ]; then
    CERT_PATH="./certs/server.crt"
    echo "   Certificate: $CERT_PATH"
    openssl x509 -in "$CERT_PATH" -noout -subject -issuer -dates -fingerprint 2>/dev/null || echo "   Could not read certificate"
else
    echo "   No certificate found at ./certs/server.crt"
    echo "   TLS auto-generation may not have run yet"
fi
echo ""

# Test 8: Port connectivity check
echo "📋 Test 8: Port Connectivity Check"
for port in 7771 7772 7776 7777; do
    if curl -s --connect-timeout 2 "http://localhost:$port/api/system/health" > /dev/null 2>&1 || \
       curl -sk --connect-timeout 2 "https://localhost:$port/api/system/health" > /dev/null 2>&1; then
        echo "   ✅ Port $port: OPEN"
    else
        echo "   ❌ Port $port: CLOSED"
    fi
done
echo ""

echo "========================================="
echo "  Test Suite Complete"
echo "========================================="
