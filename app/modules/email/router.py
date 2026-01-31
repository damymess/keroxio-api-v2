"""
Email module - send transactional emails via Resend
"""
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from pydantic import BaseModel, EmailStr
from typing import Optional, List
import httpx

from app.core.config import settings
from app.core.security import get_current_user

router = APIRouter()


class EmailSend(BaseModel):
    to: List[EmailStr]
    subject: str
    html: Optional[str] = None
    text: Optional[str] = None


class EmailTemplate(BaseModel):
    template: str  # welcome, reset_password, invoice, etc.
    to: EmailStr
    data: dict = {}


async def send_email_resend(to: List[str], subject: str, html: str = None, text: str = None):
    """Send email via Resend API"""
    if not settings.RESEND_API_KEY:
        raise HTTPException(status_code=503, detail="Email service not configured")
    
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.resend.com/emails",
            headers={
                "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "from": settings.EMAIL_FROM,
                "to": to,
                "subject": subject,
                "html": html,
                "text": text
            }
        )
        
        if response.status_code != 200:
            raise HTTPException(status_code=response.status_code, detail=response.text)
        
        return response.json()


# Email templates
TEMPLATES = {
    "welcome": {
        "subject": "Bienvenue sur Keroxio ! 🚗",
        "html": """
        <h1>Bienvenue {name} !</h1>
        <p>Merci de rejoindre Keroxio, la plateforme qui simplifie la vente automobile.</p>
        <p><a href="https://app.keroxio.fr">Commencer maintenant</a></p>
        """
    },
    "reset_password": {
        "subject": "Réinitialisation de mot de passe",
        "html": """
        <h1>Réinitialisation de mot de passe</h1>
        <p>Cliquez sur le lien ci-dessous pour réinitialiser votre mot de passe :</p>
        <p><a href="{reset_url}">Réinitialiser mon mot de passe</a></p>
        <p>Ce lien expire dans 1 heure.</p>
        """
    },
    "invoice": {
        "subject": "Votre facture Keroxio #{invoice_id}",
        "html": """
        <h1>Facture #{invoice_id}</h1>
        <p>Merci pour votre paiement de {amount}€.</p>
        <p>Votre abonnement {plan} est actif jusqu'au {end_date}.</p>
        """
    },
    "annonce_published": {
        "subject": "Votre annonce est en ligne ! 🎉",
        "html": """
        <h1>Félicitations !</h1>
        <p>Votre annonce "{title}" est maintenant publiée.</p>
        <p><a href="{annonce_url}">Voir l'annonce</a></p>
        """
    }
}


@router.post("/send")
async def send_email(
    email_data: EmailSend,
    background_tasks: BackgroundTasks,
    current_user: dict = Depends(get_current_user)
):
    """Send a custom email (admin only)"""
    if current_user.get("role") != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    background_tasks.add_task(
        send_email_resend,
        email_data.to,
        email_data.subject,
        email_data.html,
        email_data.text
    )
    
    return {"message": "Email queued", "to": email_data.to}


@router.post("/template")
async def send_template_email(
    template_data: EmailTemplate,
    background_tasks: BackgroundTasks
):
    """Send a templated email"""
    if template_data.template not in TEMPLATES:
        raise HTTPException(status_code=400, detail=f"Unknown template: {template_data.template}")
    
    template = TEMPLATES[template_data.template]
    subject = template["subject"].format(**template_data.data)
    html = template["html"].format(**template_data.data)
    
    background_tasks.add_task(
        send_email_resend,
        [template_data.to],
        subject,
        html
    )
    
    return {"message": "Email queued", "template": template_data.template}


@router.get("/templates")
async def list_templates():
    """List available email templates"""
    return {"templates": list(TEMPLATES.keys())}
