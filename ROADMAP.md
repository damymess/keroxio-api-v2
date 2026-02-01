# 🚗 KEROXIO - Feuille de Route

> Dernière mise à jour : 2026-02-01 18:04

---

## 📋 Vision Produit

**Keroxio** est une plateforme d'aide à la vente automobile pour les **garages achat/revente** et les **particuliers**.

### Workflow utilisateur :
1. 📸 **Photo du véhicule** → Lecture automatique de la plaque d'immatriculation
2. 🎨 **Nettoyage de l'image** → Suppression arrière-plan + **fonds garage pro**
3. 💰 **Estimation du prix** → Prix de vente suggéré basé sur le marché
4. ✍️ **Rédaction auto** → Annonce professionnelle générée automatiquement
5. 🚀 **Publication** → Redirection vers LeBonCoin ou LaCentrale

### Cible :
- **Pro** : Garages achat/revente (volume d'annonces)
- **Particuliers** : Vente occasionnelle simplifiée

### Objectif : **1 million d'utilisateurs**

---

## 🟢 État Actuel (2026-02-01) - PHASE 4 COMPLÈTE ✅

### Architecture consolidée : 16 → 8 services

| Service | URL | Status | Rôle |
|---------|-----|--------|------|
| **api-v2** | api.keroxio.fr | ✅ healthy | **API unifiée (10 modules)** |
| web | keroxio.fr | ✅ healthy | Landing page |
| dashboard | app.keroxio.fr | ✅ running | App principale |
| admin | admin.keroxio.fr | ✅ running | Panel admin |
| annonce | annonce.keroxio.fr | ✅ healthy | Rédaction annonces |
| immat | immat.keroxio.fr | ✅ healthy | Lecture plaques |
| pricing | pricing.keroxio.fr | ✅ healthy | Estimation prix |
| storage | storage.keroxio.fr | ✅ healthy | Stockage fichiers |

### Modules API v2 (10)
- **auth** - JWT authentication
- **billing** - Stripe payments
- **subscription** - Gestion abos
- **crm** - Leads/contacts
- **email** - Resend emails
- **notification** - Notifs in-app
- **pricing** - Estimation prix véhicules
- **immat** - Validation plaques + **OCR**
- **image** - Remove-bg + backgrounds + **masquage plaque**
- **vehicle** - **Stockage véhicules** (NEW)

---

## 🖼️ Module Image - COMPLET ✅

### Stack technique
- **Remove-bg** : remove.bg API (~0.6s, ~0.05€/image)
- **Composite** : Pillow (Python) (~0.15s)
- **Masquage plaque** : Plate Recognizer + Pillow blur
- **Total** : ~0.7s par image

### Endpoints

```
GET  /image/health              → Status module
GET  /image/backgrounds         → Liste backgrounds
POST /image/backgrounds         → Upload background

POST /image/remove-bg           → PNG transparent (URL)
POST /image/remove-bg/upload    → PNG transparent (upload)

POST /image/composite           → Voiture + fond
POST /image/process             → Pipeline complet ⚡
POST /image/process/upload      → Pipeline complet (upload)
POST /image/mask-plate          → Flouter la plaque 🆕

GET  /image/files/{filename}    → Télécharger résultat
GET  /image/backgrounds/{f}     → Servir background
POST /image/info                → Métadonnées image
```

---

## 🚗 Module Vehicle - NOUVEAU ✅

### Table PostgreSQL `vehicles`

| Champ | Type | Description |
|-------|------|-------------|
| id | UUID | Primary key |
| user_id | UUID | Owner |
| plaque | String | Immatriculation |
| marque, modele, version | String | Infos véhicule |
| annee, kilometrage | Integer | Année, km |
| carburant, boite, couleur | String | Caractéristiques |
| prix_estime_*, prix_choisi | Integer | Prix |
| photos_originales | JSON | URLs photos originales |
| photos_traitees | JSON | URLs photos traitées |
| annonce_titre, annonce_description | Text | Annonce |
| status | String | draft/ready/published |
| published_platforms | JSON | Plateformes de publication |

### Endpoints

```
POST   /vehicle              → Créer un véhicule
GET    /vehicle              → Liste mes véhicules
GET    /vehicle/{id}         → Détail véhicule
PATCH  /vehicle/{id}         → Modifier véhicule
DELETE /vehicle/{id}         → Supprimer véhicule
POST   /vehicle/{id}/publish → Marquer comme publié
```

---

## 🔍 Module Immat - OCR ACTIVÉ ✅

### Endpoints

```
GET  /immat/{plaque}         → Lookup véhicule
GET  /immat/{plaque}/validate → Valider format plaque
POST /immat/ocr              → OCR depuis image 🆕
POST /immat/ocr/full         → OCR + lookup véhicule 🆕
GET  /immat/ocr/health       → Status OCR
```

**Provider OCR** : Plate Recognizer API ✅ configuré

---

## 📅 Phases de Migration

### Phase 1 : RÉPARER L'URGENT ✅ TERMINÉ
- [x] Diagnostiquer les services crashés
- [x] Réparer auth, pricing, dashboard, gateway, storage
- [x] Solution image → rembg (mode éco)

### Phase 2 : CONSOLIDER L'API ✅ TERMINÉ
- [x] Créer `keroxio-api-v2` (FastAPI)
- [x] Migrer tous les modules
- [x] Basculer api.keroxio.fr → api-v2
- [x] **Résultat : 16 services → 8 services**

### Phase 3 : MODULE IMAGE ✅ TERMINÉ
- [x] Intégrer remove.bg API
- [x] Créer service composite Pillow
- [x] Smart auto-scaling (38% pour vue 3/4)
- [x] 7 backgrounds custom uploadés
- [x] **Résultat : ~0.7s par image, 0.05€/image**

### Phase 4 : INTÉGRATION DASHBOARD ✅ TERMINÉ
- [x] Refonte complète du dashboard (workflow 5 étapes)
- [x] UI upload photos + sélection background
- [x] Toutes les APIs connectées (image, pricing, annonce, immat)
- [x] Liens publication (LeBonCoin, LaCentrale, ParuVendu)
- [x] **OCR plaque automatique** (Plate Recognizer)
- [x] **Masquage plaque** (POST /image/mask-plate)
- [x] **Module Vehicle** (stockage PostgreSQL)

### Phase 5 : FINITIONS 🎨 EN COURS
- [ ] Brancher dashboard → API vehicle (sauvegarder les véhicules créés)
- [ ] Download/partage photos (save to gallery, share)
- [ ] Preview photos avant/après
- [ ] Améliorer UX mobile

### Phase 6 : WORKERS ASYNC 🔄
- [ ] Redis Queue pour traitement background
- [ ] Worker image (batch processing)
- [ ] Worker pricing (estimation IA)

### Phase 7 : SCALE & MONITORING 📈
- [ ] Prometheus + Grafana
- [ ] Logs centralisés
- [ ] Load testing
- [ ] Auto-scaling

---

## 🔧 Infos Techniques

### APIs intégrées
| Service | Usage | Coût |
|---------|-------|------|
| **remove.bg** | Background removal | ~0.05€/image |
| **Plate Recognizer** | OCR plaques | ~0.01€/lecture |
| **Resend** | Emails transactionnels | Gratuit (quota) |
| **Stripe** | Paiements | 1.4% + 0.25€ |

### Clés API configurées (Coolify)
- `REMOVEBG_API_KEY` ✅
- `PLATE_RECOGNIZER_API_KEY` ✅
- `AUTOBG_API_KEY` (backup)
- `RESEND_API_KEY` ✅
- `STRIPE_SECRET_KEY` ✅

### Stack
- **Backend** : Python FastAPI
- **Frontend** : Vite + React + TypeScript + TailwindCSS
- **DB** : PostgreSQL
- **Cache** : Redis
- **Storage** : Cloudflare R2
- **Deploy** : Coolify (Docker)

---

## 📝 Changelog

### 2026-02-01 18:04 - Phase 4 COMPLÈTE 🎉
- ✅ **OCR plaque automatique** - Dashboard branché sur /immat/ocr/full
- ✅ **Masquage plaque** - POST /image/mask-plate (Plate Recognizer + blur Pillow)
- ✅ **Module Vehicle** - CRUD complet, stockage PostgreSQL
- ✅ Dashboard workflow 5 étapes fonctionnel
- ✅ Toutes les APIs connectées

### 2026-02-01 17:10 - Dashboard REFAIT 📱
- ✅ Refonte complète selon vision produit originale
- ✅ Suppression CRM (hors scope)
- ✅ Workflow 5 étapes : Plaque → Photos → Prix → Annonce → Publier
- ✅ Page /new avec wizard complet
- ✅ Sidebar simplifiée

### 2026-02-01 14:10 - Module Image FINALISÉ 🖼️
- ✅ Smart auto-scaling (38% pour vue 3/4)
- ✅ 7 backgrounds custom
- ✅ Performance : ~0.7s par image

### 2026-02-01 11:00 - Migration Phase 2 complète
- ✅ api.keroxio.fr → api-v2
- ✅ Modules pricing + immat ajoutés

### 2026-01-31 21:30 - API v2 Déployée 🚀
- ✅ Créé `keroxio-api-v2` (FastAPI monolithique)
- ✅ DB dédiée `keroxio_v2`

---

## 🎯 Prochaine Action

**→ Phase 5 : Finitions**

1. [ ] Brancher dashboard → API vehicle (persist les véhicules)
2. [ ] Download/partage photos (enregistrer galerie, partager)
3. [ ] Preview photos avant/après
4. [ ] Tests E2E du flow complet
