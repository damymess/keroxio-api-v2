# 🚗 KEROXIO - Feuille de Route

> Dernière mise à jour : 2026-02-01 14:10

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

## 🟢 État Actuel (2026-02-01) - MODULE IMAGE FINALISÉ ✅

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

## 🖼️ Module Image - TERMINÉ ✅

### Stack technique
- **Remove-bg** : remove.bg API (~0.6s, ~0.05€/image)
- **Composite** : Pillow (Python) (~0.15s)
- **Total** : ~0.7s par image

### Auto-scaling intelligent
| Orientation | Ratio | Scale |
|-------------|-------|-------|
| Vue côté (landscape) | > 1.3 | 45% |
| Vue face/arrière (portrait) | < 0.8 | 30% hauteur |
| Vue 3/4 | 0.8-1.3 | **38%** |

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

GET  /image/files/{filename}    → Télécharger résultat
GET  /image/backgrounds/{f}     → Servir background
POST /image/info                → Métadonnées image
```

### Backgrounds disponibles (7 customs)

| ID | Nom | Description |
|----|-----|-------------|
| `showroom_led` | Showroom LED | LED ceiling grid premium |
| `showroom_blue` | Showroom Blue | LED strips bleus |
| `neon_cyberpunk` | Cyberpunk | Néon rose/cyan |
| `garage_concrete` | Garage Béton | Piliers béton |
| `garage_industrial` | Industriel | Lignes jaunes |
| `tunnel_led` | Tunnel LED | Tunnel néon |
| `garage_dark` | Garage Dark | Étagères sombres |

### Exemple d'utilisation

```bash
# Pipeline complet en 1 requête (scale auto à 38%)
curl -X POST https://api.keroxio.fr/image/process/upload \
  -F "file=@voiture.jpg" \
  -F "background=showroom_led"

# Réponse (~0.7s)
{
  "id": "xxx",
  "status": "completed",
  "transparent_url": "https://api.keroxio.fr/image/files/xxx_transparent.png",
  "final_url": "https://api.keroxio.fr/image/files/xxx_final.jpg",
  "background": "showroom_led",
  "processing_time": 0.72
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
- [x] Smart auto-scaling (38% pour vue 3/4)
- [x] Trim transparent pixels
- [x] 7 backgrounds custom uploadés
- [x] Endpoint `/image/process/upload` fonctionnel
- [x] **Résultat : ~0.7s par image, 0.05€/image**

### Phase 4 : INTÉGRATION DASHBOARD 🎨 À FAIRE
- [ ] Intégrer le module image dans le dashboard
- [ ] UI pour choisir le background
- [ ] Preview avant validation
- [ ] Option masquage de plaque

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

### 2026-02-01 14:10 - Module Image FINALISÉ 🖼️ ✅
- ✅ Smart auto-scaling basé sur orientation voiture
- ✅ Scale final : **38%** pour vue 3/4
- ✅ 7 backgrounds custom (showroom_led, neon_cyberpunk, etc.)
- ✅ Trim transparent pixels
- ✅ Position voiture en bas (sol)
- ✅ Performance : **~0.7s** par image
- ✅ **DOSSIER KEROXIO FERMÉ**

### 2026-02-01 13:25 - Module Image COMPLET 🖼️
- ✅ Intégration **remove.bg API** (rapide, ~0.6s)
- ✅ Composite **Pillow** local (~0.15s)
- ✅ Pipeline complet **~1s** par image
- ✅ 6 backgrounds générés automatiquement
- ✅ Endpoint `/image/process` fonctionnel

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

**→ Phase 4 : Intégration Dashboard**

1. [ ] Créer UI dans le dashboard pour uploader photo
2. [ ] Sélecteur de background avec preview
3. [ ] Affichage résultat avant/après
4. [ ] Download du résultat final
