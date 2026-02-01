# 🚗 KEROXIO - Feuille de Route

> Dernière mise à jour : 2026-02-01 12:40

---

## 📋 Vision Produit

**Keroxio** est une plateforme d'aide à la vente automobile pour les **garages achat/revente** et les **particuliers**.

### Workflow utilisateur :
1. 📸 **Photo du véhicule** → Lecture automatique de la plaque d'immatriculation
2. 🎨 **Nettoyage de l'image** → Suppression/amélioration de l'arrière-plan + **fonds garage pro**
3. 💰 **Estimation du prix** → Prix de vente suggéré basé sur le marché
4. ✍️ **Rédaction auto** → Annonce professionnelle générée automatiquement
5. 🚀 **Publication** → Redirection vers LeBonCoin ou LaCentrale

### Cible :
- **Pro** : Garages achat/revente (volume d'annonces)
- **Particuliers** : Vente occasionnelle simplifiée

### Objectif : **1 million d'utilisateurs**

---

## 🟢 État Actuel (2026-02-01)

### Architecture consolidée : 16 → 8 services

| Service | URL | Status | Rôle |
|---------|-----|--------|------|
| **api-v2** | api.keroxio.fr | ✅ healthy | **API unifiée (9 modules)** |
| web | keroxio.fr | ✅ healthy | Landing page |
| dashboard | app.keroxio.fr | ✅ running | App principale |
| admin | admin.keroxio.fr | ✅ running | Panel admin |
| annonce | annonce.keroxio.fr | ✅ healthy | Rédaction annonces |
| immat | immat.keroxio.fr | ✅ healthy | Lecture plaques |
| pricing | pricing.keroxio.fr | ✅ healthy | Estimation prix |
| storage | storage.keroxio.fr | ✅ healthy | Stockage fichiers |

### ❌ Services supprimés (migrés vers api-v2)
- ~~auth~~ → module auth
- ~~gateway~~ → api-v2
- ~~billing~~ → module billing
- ~~subscription~~ → module subscription
- ~~crm~~ → module crm
- ~~email~~ → module email
- ~~notification~~ → module notification
- ~~image (legacy)~~ → module image

---

## 🆕 API v2 - Architecture Unifiée

**URL** : https://api.keroxio.fr (+ alias api-v2.keroxio.fr)
**Status** : ✅ running:healthy
**Stack** : FastAPI + PostgreSQL + Redis

### Modules inclus (9) :

| Module | Endpoints | Description |
|--------|-----------|-------------|
| auth | `/auth/*` | Register, Login, JWT |
| billing | `/billing/*` | Stripe Checkout, Plans |
| subscription | `/subscription/*` | Gestion abos |
| crm | `/crm/*` | Leads, Contacts, Stats |
| email | `/email/*` | Emails (Resend) |
| notification | `/notification/*` | Notifs in-app |
| pricing | `/pricing/*` | Estimation prix véhicule |
| immat | `/immat/*` | Validation plaques |
| **image** | `/image/*` | **Remove-bg + Backgrounds pro** |

### 🖼️ Module Image (nouveau)

**Fonctionnalités :**
- Suppression arrière-plan via **AutoBG.ai**
- Application de **fonds professionnels**
- Ombres et reflets réalistes
- Pipeline complet en une requête

**Arrière-plans disponibles :**
| ID | Nom | Type |
|----|-----|------|
| `showroom_indoor` | Showroom Intérieur | Image |
| `showroom_outdoor` | Showroom Extérieur | Image |
| `studio_white` | Studio Blanc | Dégradé |
| `studio_grey` | Studio Gris | Dégradé |
| `studio_black` | Studio Noir | Dégradé |
| `garage_modern` | Garage Moderne | Image |
| `garage_luxury` | Garage Luxe | Image |
| `parking_outdoor` | Parking Extérieur | Image |

**Endpoints :**
```
GET  /image/health                → Status module
GET  /image/backgrounds           → Liste tous les fonds
GET  /image/backgrounds/{cat}     → Fonds par catégorie

POST /image/remove-bg             → Supprime le fond (URL)
POST /image/remove-bg/upload      → Supprime le fond (upload)

POST /image/apply-background      → Applique un fond pro
POST /image/process               → Pipeline complet (remove + apply)
POST /image/process/upload        → Pipeline complet (upload)

POST /image/info                  → Métadonnées image
POST /image/resize                → Redimensionner
```

**Options apply-background :**
- `background_type` : Type de fond
- `scale` : Échelle voiture (0.5-2.0)
- `position_x/y` : Position (0.0-1.0)
- `add_shadow` : Ombre réaliste
- `add_reflection` : Reflet showroom

---

## 🎯 Architecture Cible

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
                    │   API v2    │  ← scale horizontal
                    │  (FastAPI)  │
                    │             │
                    │ 9 Modules:  │
                    │ auth,billing│
                    │ crm,email   │
                    │ notif,sub   │
                    │ pricing     │
                    │ immat,image │
                    └──────┬──────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                 ▼
    PostgreSQL          Redis           Storage
   (keroxio_v2)        (cache)      (storage.keroxio.fr)
```

---

## 📅 Phases de Migration

### Phase 1 : RÉPARER L'URGENT ✅ TERMINÉ
- [x] Diagnostiquer les services crashés
- [x] Réparer auth, pricing, dashboard, gateway, storage
- [x] Solution image → rembg (mode éco)

### Phase 2 : CONSOLIDER L'API ✅ TERMINÉ
- [x] Créer `keroxio-api-v2` (FastAPI)
- [x] Migrer tous les modules (auth, billing, crm, email, notif, subscription)
- [x] Ajouter modules pricing + immat
- [x] **Ajouter module image (remove-bg + backgrounds pro)**
- [x] Basculer api.keroxio.fr → api-v2
- [x] Supprimer les 10 anciens microservices
- [x] **Résultat : 16 services → 8 services**

### Phase 3 : ASSETS & POLISH 🎨 EN COURS
- [ ] **Uploader les images de fond sur storage.keroxio.fr**
- [ ] Créer les thumbnails pour preview
- [ ] Intégrer le module image dans le dashboard
- [ ] Tests end-to-end du pipeline photo

### Phase 4 : WORKERS ASYNC 🔄
- [ ] Redis Queue pour traitement background
- [ ] Worker image (batch processing)
- [ ] Worker pricing (estimation IA)

### Phase 5 : SCALE & MONITORING 📈
- [ ] Prometheus + Grafana
- [ ] Logs centralisés
- [ ] Load testing
- [ ] Auto-scaling

---

## 🔧 Infos Techniques

### APIs intégrées
- **AutoBG.ai** : Background removal (clé configurée)
- **Resend** : Emails transactionnels
- **Stripe** : Paiements (live)

### Coolify
- **URL** : https://control.maisons-amgr.com
- **API Token** : `3|7DEbDLj6...`

### Stack
- **Backend** : Python FastAPI
- **Frontend** : Next.js/Vite + TypeScript + TailwindCSS
- **DB** : PostgreSQL
- **Cache** : Redis
- **Storage** : MinIO (S3-compatible)
- **Deploy** : Coolify (Docker)

---

## 📝 Changelog

### 2026-02-01 12:40 - Module Image + Backgrounds Pro 🖼️
- ✅ Ajout module `/image` dans api-v2
- ✅ Intégration AutoBG.ai pour remove-bg
- ✅ 8 arrière-plans pro (showroom, studio, garage, outdoor)
- ✅ Support ombres et reflets
- ✅ Pipeline complet (remove + apply en 1 requête)
- ✅ Endpoints upload direct
- ✅ Suppression 10 anciens microservices
- ✅ Architecture finale : **8 services**

### 2026-02-01 11:00 - Migration Phase 2 complète
- ✅ Dashboard connecté à api-v2
- ✅ api.keroxio.fr → pointe vers api-v2
- ✅ Modules pricing + immat ajoutés

### 2026-01-31 21:30 - API v2 Déployée 🚀
- ✅ Créé `keroxio-api-v2` (FastAPI monolithique)
- ✅ Modules: auth, billing, subscription, crm, email, notification
- ✅ DB dédiée `keroxio_v2`
- ✅ Status: running:healthy

### 2026-01-31 18:43 - Service Image réparé
- Simplifié: rembg au lieu de BiRefNet
- 5GB → 500MB de dépendances

---

## 🎯 Prochaine Action

**→ Phase 3 : Uploader les images de fond**

1. [ ] Créer/trouver 5 images pro (1920x1080) :
   - `showroom-indoor.jpg`
   - `showroom-outdoor.jpg`
   - `garage-modern.jpg`
   - `garage-luxury.jpg`
   - `parking-outdoor.jpg`
2. [ ] Upload sur `storage.keroxio.fr/backgrounds/`
3. [ ] Créer thumbnails 400x225
4. [ ] Tester le pipeline complet

**URLs :**
- API: https://api.keroxio.fr
- Health: https://api.keroxio.fr/image/health
- Backgrounds: https://api.keroxio.fr/image/backgrounds
