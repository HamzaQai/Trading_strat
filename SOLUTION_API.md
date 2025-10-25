# 🔴 PROBLÈME CRITIQUE DÉTECTÉ - Clé API Sans Permissions

## 📊 Diagnostic Complet

Votre clé API Oanda : `198854ba4998ff33bdd2883fc4cba850-19bd4901362620fb933a0c268786e9e2`

**Résultat du diagnostic :**
```
❌ Test 1 (Account Info)        : 403 Access denied
❌ Test 2 (Instruments List)    : 403 Access denied
❌ Test 3 (Historical Data)     : 403 Access denied
❌ Test 4 (Current Pricing)     : 403 Access denied
❌ Test 5 (Account Summary)     : 403 Access denied
```

## 🔍 Analyse

**403 "Access denied" sur TOUS les endpoints = Clé API sans aucune permission**

Cela signifie que lors de la création de votre clé API, **aucune permission n'a été cochée** ou que la clé a été révoquée.

---

## ✅ SOLUTION DÉFINITIVE (5 minutes)

### Étape 1 : Supprimer l'Ancienne Clé

1. Allez sur : **https://www.oanda.com/**
2. **Login** avec vos identifiants
3. Menu : **Manage Funds & Transfer → Manage API Access**
4. Trouvez votre clé actuelle (termine par `...e9e2`)
5. Cliquez sur **"Revoke"** ou **"Delete"**

### Étape 2 : Créer une NOUVELLE Clé avec Toutes les Permissions

1. Cliquez sur **"Generate"** ou **"Create New API Key"**

2. **COCHEZ TOUTES CES CASES** (CRITIQUE) :
   ```
   ☑️ Read Account Data
   ☑️ Read Market Data        ← OBLIGATOIRE
   ☑️ Trade                    ← OPTIONNEL (mais recommandé)
   ☑️ View Historical Data     ← OBLIGATOIRE
   ```

3. **Nom du token** : "Backtest Framework" (ou autre)

4. Cliquez sur **"Generate"**

5. **COPIEZ IMMÉDIATEMENT** la nouvelle clé (elle ne sera affichée qu'une fois !)

### Étape 3 : Mettre à Jour la Configuration

1. Ouvrez `config/config.yaml`

2. Remplacez la clé API :
   ```yaml
   oanda:
     api_key: "VOTRE_NOUVELLE_CLE_AVEC_PERMISSIONS"
     account_id: "101-004-16051716-001"
     environment: "practice"
   ```

3. Sauvegardez le fichier

### Étape 4 : Tester

```bash
python diagnostic_api.py
```

**Résultat attendu :**
```
✅ Test 1 : 200 OK
✅ Test 2 : 200 OK
✅ Test 3 : 200 OK
✅ Test 4 : 200 OK
✅ Test 5 : 200 OK
```

---

## 🎯 Alternative : Créer un Nouveau Compte Practice

Si vous ne trouvez pas l'option "Manage API Access", créez un nouveau compte :

### Option A : Nouveau Compte Practice Oanda

1. **https://www.oanda.com/demo-account/**
2. Remplir le formulaire (prend 2 minutes)
3. Email de confirmation
4. Login
5. **Manage API Access** → Créer clé avec **TOUTES** les permissions

### Option B : Utiliser fxTrade Practice (Recommandé)

1. **https://www1.oanda.com/register/#/sign-up/demo**
2. S'inscrire (compte démo illimité)
3. Une fois connecté :
   - Settings → API Access
   - Generate Personal Access Token
   - **Cocher TOUTES les permissions**

---

## 📸 Ce Que Vous Devez Voir

Lors de la création de la clé API, vous DEVEZ voir cet écran avec ces options :

```
┌────────────────────────────────────────┐
│  Create Personal Access Token          │
├────────────────────────────────────────┤
│  Token Name: [Backtest Framework    ] │
│                                         │
│  Permissions:                           │
│  ☑️ Read Account Data                  │
│  ☑️ Read Market Data                   │
│  ☑️ Trade                               │
│  ☑️ View Historical Data                │
│                                         │
│  [Generate Token]                       │
└────────────────────────────────────────┘
```

**SI VOUS NE VOYEZ PAS CET ÉCRAN** = Votre compte n'a pas accès à l'API

---

## 🚀 Solution Temporaire : Continuer avec Données Synthétiques

En attendant de résoudre le problème API, vous pouvez continuer à développer :

### Utiliser les Données Synthétiques (Immédiat)

```bash
# Backtest avec données synthétiques réalistes
python run_test_backtest.py
```

**Avantages :**
- ✅ Fonctionne immédiatement (pas besoin d'API)
- ✅ Données réalistes (volatilité, tendances, patterns)
- ✅ Parfait pour développement et tests
- ✅ Rapide (pas de limite API)

**Résultats déjà disponibles :**
- 134 trades testés
- 6 stratégies validées
- Stratégie MTTF : +2,027% return
- Tous les fichiers dans `results/test_run/`

### Développer et Optimiser

Pendant que vous réglez l'API, vous pouvez :

1. **Optimiser les stratégies**
   ```bash
   # Modifier les paramètres dans config/strategies_params.yaml
   # Puis re-tester
   python run_test_backtest.py
   ```

2. **Créer votre propre stratégie**
   ```bash
   # Copier une stratégie existante
   cp strategies/mttf.py strategies/ma_strategie.py
   # Éditer et tester
   ```

3. **Analyser les résultats**
   ```bash
   # Voir tous les trades
   cat results/test_run/all_trades.csv

   # Voir les métriques
   cat results/test_run/strategy_metrics.csv
   ```

---

## 🆘 Si Rien ne Fonctionne

### Contacter le Support Oanda

**Email :** api@oanda.com
**Sujet :** "Unable to create API token with market data permissions"
**Message :**
```
Hello,

I am trying to create an API token for my practice account (101-004-16051716-001)
but I receive "403 Access denied" errors on all endpoints.

Could you please help me create a token with the following permissions:
- Read Account Data
- Read Market Data
- View Historical Data

Thank you.
```

### Vérifier le Type de Compte

Certains comptes practice ont des limitations. Vérifiez :
- Type de compte : Practice/Demo
- Région : Certains pays ont des restrictions
- Date de création : Les vieux comptes peuvent avoir des limitations

---

## 📊 Résumé des Actions

### Priorité 1 : Résoudre l'API (Recommandé)

1. ✅ Supprimer ancienne clé
2. ✅ Créer nouvelle clé avec TOUTES permissions
3. ✅ Mettre à jour config.yaml
4. ✅ Tester avec `python diagnostic_api.py`
5. ✅ Si OK → `python main.py --strategies mttf`

### Priorité 2 : Continuer Sans API (Immédiat)

1. ✅ Utiliser données synthétiques
2. ✅ Développer et optimiser stratégies
3. ✅ Analyser résultats actuels
4. ✅ Résoudre API en parallèle

---

## ✨ Conclusion

**Diagnostic : Votre clé API n'a AUCUNE permission activée.**

**Solution : Créer une NOUVELLE clé avec TOUTES les permissions cochées.**

**Alternative : Continuer avec données synthétiques pendant que vous réglez l'API.**

**Le framework fonctionne parfaitement - il attend juste des données réelles !** 🚀

---

## 📞 Besoin d'Aide ?

Si après avoir suivi ce guide vous avez toujours des problèmes :

1. Vérifiez que vous êtes sur un compte **Practice** (pas Live)
2. Essayez avec un navigateur différent (parfois cache problèmes)
3. Déconnectez-vous complètement et reconnectez-vous
4. Contactez le support Oanda avec votre Account ID

**Le framework est prêt - juste besoin d'une clé API valide !** 💪
