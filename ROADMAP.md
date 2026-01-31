# 🚗 KEROXIO - Feuille de Route

> Dernière mise à jour : 2026-01-31 21:30

---

## 📋 Vision Produit

**Keroxio** est une plateforme d'aide à la vente automobile pour les **garages achat/revente** et les **particuliers**.

### Workflow utilisateur :
1. 📸 **Photo du véhicule** → Lecture automatique de la plaque d'immatriculation
2. 🎨 **Nettoyage de l'image** → Suppression/amélioration de l'arrière-plan
3. 💰 **Estimation du prix** → Prix de vente suggéré basé sur le marché
4. ✍️ **Rédaction auto** → Annonce professionnelle générée automatiquement
5. 🚀 **Publication** → Redirection vers LeBonCoin ou LaCentrale

### Cible :
- **Pro** : Garages achat/revente (volume d'annonces)
- **Particuliers** : Vente occasionnelle simplifiée

### Objectif : **1 million d'utilisateurs**

---

## 🔴 État Actuel (2026-01-31)

### Services déployés sur Coolify :

| Service | URL | Status | Rôle |
|---------|-----|--------|------|
| web | keroxio.fr | ✅ Running | Landing page |
| admin | admin.keroxio.fr | ✅ Running | Panel admin |
| annonce | annonce.keroxio.fr | ✅ Running | Rédaction annonces |
| immat | immat.keroxio.fr | ✅ Running | Lecture plaques |
| **auth** | auth.keroxio.fr | ✅ Running | Authentification (legacy) |
| **gateway** | api.keroxio.fr | ✅ Running | API Gateway (legacy) |
| **pricing** | pricing.keroxio.fr | ✅ Running | Estimation prix |
| **dashboard** | app.keroxio.fr | ✅ Running | App principale |
| **storage** | storage.keroxio.fr | ✅ Running | Stockage fichiers |
| **image** | image.keroxio.fr | ✅ Running | rembg (mode éco, self-hosted) |
| **🆕 api-v2** | api-v2.keroxio.fr | ✅ **Running:Healthy** | **Nouvelle API unifiée** |
| ~~billing~~ | billing.keroxio.fr | 🔄 Migré → api-v2 | |
| ~~crm~~ | crm.keroxio.fr | 🔄 Migré → api-v2 | |
| ~~email~~ | mail.keroxio.fr | 🔄 Migré → api-v2 | |
| ~~subscription~~ | sub.keroxio.fr | 🔄 Migré → api-v2 | |
| ~~notification~~ | notif.keroxio.fr | 🔄 Migré → api-v2 | |

### 🆕 API v2 - Nouvelle Architecture Unifiée

**URL** : https://api-v2.keroxio.fr
**Status** : ✅ running:healthy
**Database** : PostgreSQL `keroxio_v2` (dédiée)

**Modules inclus :**
- `/auth` - Register, Login, JWT
- `/billing` - Stripe Checkout, Webhooks, Plans
- `/subscription` - Gestion abonnements
- `/crm` - Leads, Contacts, Stats
- `/email` - Emails transactionnels (Resend)
- `/notification` - Notifications in-app

**Endpoints disponibles :**
```
GET  /health              → {"status": "healthy", "version": "2.0.0"}
GET  /                    → Info API + modules

POST /auth/register       → Inscription
POST /auth/login          → Connexion
GET  /auth/me             → Profil utilisateur

POST /billing/create-checkout-session
POST /billing/webhook
GET  /billing/plans

GET  /subscription/current
GET  /subscription/usage
POST /subscription/cancel

POST /crm/leads
GET  /crm/leads
GET  /crm/stats

POST /email/send
POST /email/template

GET  /notification/
POST /notification/{id}/read
POST /notification/read-all
```

### Infra :
- ✅ PostgreSQL x2 + `keroxio_v2` (nouvelle DB pour api-v2)
- ✅ Redis
- ✅ MinIO (S3)
- Hébergement : Coolify sur VPS

---

## 🎯 Architecture Cible

### Principe : **4-5 services bien faits > 16 services bancals**

```
┌─────────────────────────────────────────────────────┐
│                  CDN (Cloudflare)                   │
├─────────────────┬─────────────────┬─────────────────┤
│   keroxio.fr    │  app.keroxio.fr │ admin.keroxio.fr│
│   (landing)     │   (dashboard)   │    (admin)      │
│    [static]     │    [static]     │    [static]     │
└─────────────────┴────────┬────────┴─────────────────┘
                           │
                    ┌──────▼──────┐
                    │  API v2     │  ← scale horizontal
                    │  (FastAPI)  │
                    │             │
                    │ Modules:    │
                    │ - auth      │
                    │ - billing   │
                    │ - crm       │
                    │ - email     │
                    │ - notif     │
                    │ - subscr.   │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    PostgreSQL          Redis            Queue
   (keroxio_v2)        (cache)        (Bull/Redis)
                                           │
                    ┌──────────────────────┴───────────────────────┐
                    ▼                      ▼                       ▼
             ┌─────────────┐        ┌─────────────┐        ┌─────────────┐
             │   Worker    │        │   Worker    │        │   Worker    │
             │   Image     │        │   Immat     │        │   Pricing   │
             │ (nettoyage) │        │ (API SIV)   │        │ (estimation)│
             └─────────────┘        └─────────────┘        └─────────────┘
```

---

## 📅 Phases de Migration

### Phase 1 : RÉPARER L'URGENT 🔥 ✅ TERMINÉ
**Objectif** : App fonctionnelle avec l'architecture actuelle

- [x] Diagnostiquer pourquoi les 10 services crashent
- [x] Réparer les services critiques (auth, pricing, dashboard, gateway, storage)
- [x] Décider solution image → **rembg** (mode éco, self-hosted, gratuit)
- [x] Réparer service image

### Phase 2 : CONSOLIDER L'API 🏗️ ✅ EN COURS (80%)
**Objectif** : Un seul backend au lieu de 8

- [x] Créer le nouveau repo `keroxio-api-v2` ✅
- [x] Migrer les modules :
  - [x] auth → module auth ✅
  - [x] billing → module billing ✅
  - [x] crm → module crm ✅
  - [x] subscription → module subscription ✅
  - [x] email → module email ✅
  - [x] notification → module notification ✅
- [x] Configurer les variables d'environnement ✅
- [x] Créer DB dédiée `keroxio_v2` ✅
- [x] Déployer sur https://api-v2.keroxio.fr ✅ running:healthy
- [x] Configurer domaine + SSL ✅
- [ ] **Tester tous les endpoints**
- [ ] **Connecter le dashboard à api-v2**
- [ ] **Basculer api.keroxio.fr → api-v2**
- [ ] Supprimer les anciens microservices

### Phase 3 : WORKERS ASYNC 🔄
**Objectif** : Traitement d'images et IA en background
**Durée estimée** : 1 semaine

- [ ] Mettre en place Redis Queue (ou Bull)
- [ ] Créer `media-worker` (images)
- [ ] Créer `pricing-worker` (estimation IA)

### Phase 4 : FRONTENDS STATIQUES 📱
**Objectif** : Frontends optimisés + CDN

- [ ] Configurer les builds statiques
- [ ] Configurer Cloudflare CDN
- [ ] Optimiser les assets

### Phase 5 : SCALE & MONITORING 📈
**Objectif** : Prêt pour 1M users

- [ ] Monitoring (Prometheus + Grafana)
- [ ] Logs centralisés
- [ ] Alertes
- [ ] Load testing
- [ ] Auto-scaling workers

---

## 🔧 Infos Techniques

### Coolify
- **URL** : https://control.maisons-amgr.com
- **API Token** : `3|7DEbDLj6KNrmiIna4wHmMSXPQ65KXiDz8HVnLK8ad3c70941`
- **Project** : keroxio.fr (environment: production)

### GitHub
- **Owner** : damymess
- **Repos** : Tous publics

### Databases
- **Legacy** : `postgres` (anciennes tables)
- **API v2** : `keroxio_v2` (nouvelle DB propre, UUIDs)

### Stack
- **Backend** : Python FastAPI
- **Frontend** : Next.js + TypeScript + TailwindCSS
- **DB** : PostgreSQL
- **Cache** : Redis
- **Storage** : MinIO (S3-compatible)
- **Deploy** : Coolify (Docker)

---

## 📝 Changelog

### 2026-01-31 21:30 - API v2 Déployée 🚀
- ✅ Créé `keroxio-api-v2` (FastAPI monolithique)
- ✅ Modules: auth, billing, subscription, crm, email, notification
- ✅ DB dédiée `keroxio_v2` créée
- ✅ Fix: email-validator manquant
- ✅ Fix: conflit schéma UUID vs integer (DB séparée)
- ✅ Domaine configuré: https://api-v2.keroxio.fr
- ✅ SSL automatique via Coolify/Traefik
- ✅ Status: running:healthy

### 2026-01-31 18:43 - Service Image réparé
- Simplifié: rembg (U2-Net) au lieu de BiRefNet
- 5GB → 500MB de dépendances

### 2026-01-31 17:30 - Auth, Pricing, Storage réparés
- JWT_SECRET ajouté aux services

### 2026-01-31 15:00 - Dashboard + Gateway réparés
- Problème SSH résolu

---

## 🎯 Prochaine Action

**→ Phase 2 suite : Connecter le dashboard à l'API v2**

1. ✅ API v2 déployée et healthy
2. [ ] Tester tous les endpoints (register, login, billing, etc.)
3. [ ] Modifier le dashboard pour pointer vers api-v2.keroxio.fr
4. [ ] Tester le workflow complet
5. [ ] Basculer le trafic (api.keroxio.fr → api-v2)

**URLs :**
- Landing: https://keroxio.fr
- Dashboard: https://app.keroxio.fr
- API v2: https://api-v2.keroxio.fr
- API legacy: https://api.keroxio.fr
