# Keroxio API v2

API backend unifiée pour Keroxio - Plateforme d'aide à la vente automobile.

## Architecture

Cette API consolide les anciens microservices en un seul backend :

| Module | Ancien service | Description |
|--------|---------------|-------------|
| auth | keroxio-auth | Authentification JWT |
| billing | keroxio-billing | Paiements Stripe |
| subscription | keroxio-subscription | Gestion abonnements |
| crm | keroxio-crm | Gestion leads/contacts |
| email | keroxio-email | Emails transactionnels (Resend) |
| notification | keroxio-notification | Notifications in-app |

## Stack

- **FastAPI** - Framework web async
- **PostgreSQL** - Base de données (via SQLAlchemy async)
- **Redis** - Cache (optionnel)
- **Stripe** - Paiements
- **Resend** - Emails

## Développement

```bash
# Installer les dépendances
pip install -r requirements.txt

# Variables d'environnement
cp .env.example .env
# Éditer .env avec vos valeurs

# Lancer en dev
uvicorn app.main:app --reload

# API docs
# http://localhost:8000/docs
```

## Déploiement (Docker)

```bash
# Build
docker build -t keroxio-api-v2 .

# Run
docker run -p 8000:8000 --env-file .env keroxio-api-v2
```

## Endpoints

### Auth
- `POST /auth/register` - Inscription
- `POST /auth/login` - Connexion
- `GET /auth/me` - Profil utilisateur

### Billing
- `POST /billing/create-checkout-session` - Créer session Stripe
- `POST /billing/webhook` - Webhook Stripe
- `GET /billing/plans` - Liste des plans

### Subscription
- `GET /subscription/current` - Abonnement actuel
- `GET /subscription/usage` - Utilisation
- `POST /subscription/cancel` - Annuler

### CRM
- `POST /crm/leads` - Créer un lead
- `GET /crm/leads` - Lister les leads (admin)
- `GET /crm/stats` - Statistiques

### Email
- `POST /email/send` - Envoyer email (admin)
- `POST /email/template` - Envoyer template

### Notification
- `GET /notification/` - Liste notifications
- `POST /notification/{id}/read` - Marquer comme lu
- `POST /notification/read-all` - Tout marquer lu

## Variables d'environnement

| Variable | Description | Required |
|----------|-------------|----------|
| DATABASE_URL | URL PostgreSQL | ✅ |
| JWT_SECRET | Clé secrète JWT | ✅ |
| STRIPE_SECRET_KEY | Clé API Stripe | Pour billing |
| STRIPE_WEBHOOK_SECRET | Secret webhook Stripe | Pour billing |
| RESEND_API_KEY | Clé API Resend | Pour emails |
| REDIS_URL | URL Redis | Optionnel |
