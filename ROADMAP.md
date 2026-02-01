# 🚗 KEROXIO - Feuille de Route

> Dernière mise à jour : 2026-02-01 13:25

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

---

## 🆕 API v2 - Architecture Unifiée

**URL** : https://api.keroxio.fr
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
| **image** | `/image/*` | ✅ **Remove-bg + Backgrounds pro** |

---

## 🖼️ Module Image - OPÉRATIONNEL ✅

### Stack technique
- **Remove-bg** : remove.bg API (~0.6s, ~0.05€/image)
- **Composite** : Pillow (Python) (~0.15s)
- **Total** : ~1s par image

### Endpoints

```
GET  /image/health              → Status module
GET  /image/backgrounds         → Liste les 6 fonds

POST /image/remove-bg           → PNG transparent (URL)
POST /image/remove-bg/upload    → PNG transparent (upload)

POST /image/composite           → Voiture + fond
POST /image/process             → Pipeline complet ⚡
POST /image/process/upload      → Pipeline complet (upload)

GET  /image/files/{filename}    → Télécharger résultat
POST /image/info                → Métadonnées image
```

### Backgrounds disponibles (6)

| ID | Nom | Description |
|----|-----|-------------|
| `showroom` | Showroom | Fond showroom moderne bleuté |
| `studio_white` | Studio Blanc | Fond blanc épuré |
| `studio_grey` | Studio Gris | Fond gris neutre |
| `studio_black` | Studio Noir | Fond noir premium |
| `garage_modern` | Garage Moderne | Sol époxy sombre |
| `outdoor` | Extérieur | Ciel + asphalte |

### Exemple d'utilisation

```bash
# Pipeline complet en 1 requête
curl -X POST https://api.keroxio.fr/image/process \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://...",
    "background": "studio_black",
    "position": "center",
    "scale": 0.85
  }'

# Réponse (~1s)
{
  "id": "xxx",
  "status": "completed",
  "transparent_url": "https://api.keroxio.fr/image/files/xxx_transparent.png",
  "final_url": "https://api.keroxio.fr/image/files/xxx_final.jpg",
  "background": "studio_black",
  "processing_time": 0.91
}
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
- [x] Basculer api.keroxio.fr → api-v2
- [x] Supprimer les 10 anciens microservices
- [x] **Résultat : 16 services → 8 services**

### Phase 3 : MODULE IMAGE ✅ TERMINÉ
- [x] Intégrer remove.bg API
- [x] Créer service composite Pillow
- [x] Générer 6 backgrounds par défaut
- [x] Endpoint `/image/process` (pipeline complet)
- [x] Servir les fichiers via `/image/files/`
- [x] **Résultat : ~1s par image, 0.05€/image**

### Phase 4 : ASSETS & POLISH 🎨 EN COURS
- [ ] Ajouter des backgrounds photo réels (vrais garages/showrooms)
- [ ] Intégrer le module image dans le dashboard
- [ ] Option masquage de plaque
- [ ] Tests end-to-end du pipeline photo

### Phase 5 : WORKERS ASYNC 🔄
- [ ] Redis Queue pour traitement background
- [ ] Worker image (batch processing)
- [ ] Worker pricing (estimation IA)

### Phase 6 : SCALE & MONITORING 📈
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
| **Resend** | Emails transactionnels | Gratuit (quota) |
| **Stripe** | Paiements | 1.4% + 0.25€ |

### Clés API configurées (Coolify)
- `REMOVEBG_API_KEY` ✅
- `AUTOBG_API_KEY` (backup)
- `RESEND_API_KEY` ✅
- `STRIPE_SECRET_KEY` ✅

### Stack
- **Backend** : Python FastAPI
- **Frontend** : Next.js/Vite + TypeScript + TailwindCSS
- **DB** : PostgreSQL
- **Cache** : Redis
- **Storage** : Cloudflare R2
- **Deploy** : Coolify (Docker)

---

## 📝 Changelog

### 2026-02-01 13:25 - Module Image COMPLET 🖼️ ✅
- ✅ Intégration **remove.bg API** (rapide, ~0.6s)
- ✅ Composite **Pillow** local (~0.15s)
- ✅ Pipeline complet **~1s** par image
- ✅ **6 backgrounds** générés automatiquement
- ✅ Endpoint `/image/process` fonctionnel
- ✅ Fichiers servis via `/image/files/`
- ✅ Coût : **~0.05€/image**
- ✅ Testé avec succès (Mustang → showroom/studio_black)

### 2026-02-01 12:40 - Début module Image
- Testé AutoBG.ai (trop lent/complexe)
- Décision : remove.bg + composite local

### 2026-02-01 11:00 - Migration Phase 2 complète
- ✅ Dashboard connecté à api-v2
- ✅ api.keroxio.fr → pointe vers api-v2
- ✅ Modules pricing + immat ajoutés

### 2026-01-31 21:30 - API v2 Déployée 🚀
- ✅ Créé `keroxio-api-v2` (FastAPI monolithique)
- ✅ Modules: auth, billing, subscription, crm, email, notification
- ✅ DB dédiée `keroxio_v2`

---

## 🎯 Prochaine Action

**→ Phase 4 : Améliorer les backgrounds**

1. [ ] Trouver/créer des images de fond photo réalistes
2. [ ] Uploader via `POST /image/backgrounds`
3. [ ] Intégrer dans le dashboard Keroxio
4. [ ] Option masquage de plaque d'immatriculation
