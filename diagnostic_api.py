"""
Diagnostic complet de l'API Oanda.
"""

import requests
import json

API_KEY = "198854ba4998ff33bdd2883fc4cba850-19bd4901362620fb933a0c268786e9e2"
ACCOUNT_ID = "101-004-16051716-001"
BASE_URL = "https://api-fxpractice.oanda.com"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

print("="*70)
print("🔍 DIAGNOSTIC COMPLET API OANDA")
print("="*70)

# Test 1: Account Info
print("\n📌 TEST 1: Informations du compte")
print("-"*70)
try:
    url = f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}"
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Accès au compte: OK")
        data = response.json()
        if 'account' in data:
            account = data['account']
            print(f"   Balance: {account.get('balance', 'N/A')}")
            print(f"   Currency: {account.get('currency', 'N/A')}")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 2: List Instruments
print("\n📌 TEST 2: Liste des instruments disponibles")
print("-"*70)
try:
    url = f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/instruments"
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Liste instruments: OK")
        data = response.json()
        if 'instruments' in data:
            instruments = data['instruments'][:5]  # First 5
            print(f"   Nombre d'instruments: {len(data['instruments'])}")
            print("   Premiers instruments:")
            for inst in instruments:
                print(f"      - {inst.get('name', 'N/A')}")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 3: Market Data (Historical Candles)
print("\n📌 TEST 3: Données historiques (EUR/USD)")
print("-"*70)
try:
    url = f"{BASE_URL}/v3/instruments/EUR_USD/candles"
    params = {
        "count": 10,
        "granularity": "D",
        "price": "M"
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Données historiques: OK")
        data = response.json()
        if 'candles' in data:
            candles = data['candles']
            print(f"   Nombre de bougies: {len(candles)}")
            if candles:
                last = candles[-1]
                print(f"   Dernière bougie:")
                print(f"      Time: {last.get('time', 'N/A')}")
                print(f"      Close: {last.get('mid', {}).get('c', 'N/A')}")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Response: {response.text[:500]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 4: Current Pricing
print("\n📌 TEST 4: Prix actuels (EUR/USD)")
print("-"*70)
try:
    url = f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/pricing"
    params = {
        "instruments": "EUR_USD"
    }
    response = requests.get(url, headers=headers, params=params, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Prix actuels: OK")
        data = response.json()
        if 'prices' in data and data['prices']:
            price = data['prices'][0]
            print(f"   Instrument: {price.get('instrument', 'N/A')}")
            print(f"   Bid: {price.get('bids', [{}])[0].get('price', 'N/A')}")
            print(f"   Ask: {price.get('asks', [{}])[0].get('price', 'N/A')}")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

# Test 5: Account Summary
print("\n📌 TEST 5: Résumé du compte")
print("-"*70)
try:
    url = f"{BASE_URL}/v3/accounts/{ACCOUNT_ID}/summary"
    response = requests.get(url, headers=headers, timeout=10)
    print(f"Status: {response.status_code}")
    if response.status_code == 200:
        print("✅ Résumé compte: OK")
        data = response.json()
        if 'account' in data:
            acc = data['account']
            print(f"   Balance: {acc.get('balance', 'N/A')}")
            print(f"   NAV: {acc.get('NAV', 'N/A')}")
            print(f"   Unrealized P/L: {acc.get('unrealizedPL', 'N/A')}")
    else:
        print(f"❌ Erreur: {response.status_code}")
        print(f"   Response: {response.text[:200]}")
except Exception as e:
    print(f"❌ Exception: {e}")

print("\n" + "="*70)
print("📊 RÉSUMÉ DU DIAGNOSTIC")
print("="*70)
print("\nSi tous les tests montrent 200 OK ✅ : L'API fonctionne parfaitement!")
print("Si certains tests montrent 403 ❌ : Problème de permissions")
print("Si tous montrent 401 ❌ : Clé API invalide")
print("="*70)
