"""
Servicio de envío de emails usando Gmail SMTP.
Configurado para MVP - fácil de usar con Gmail.
"""
import smtplib
import logging
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Optional, Dict, Any

logger = logging.getLogger(__name__)


class EmailService:
    """Servicio para enviar emails usando Gmail SMTP."""
    
    def __init__(
        self,
        smtp_host: str = "smtp.gmail.com",
        smtp_port: int = 587,
        smtp_user: str = "",  # Tu email de Gmail
        smtp_password: str = "",  # Tu App Password de Gmail
        from_email: str = "",  # Email que aparecerá como remitente
        from_name: str = "RIM - Sistema Inteligente de Moto"
    ):
        self.smtp_host = smtp_host
        self.smtp_port = smtp_port
        self.smtp_user = smtp_user
        self.smtp_password = smtp_password
        self.from_email = from_email or smtp_user
        self.from_name = from_name
    
    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        plain_content: Optional[str] = None
    ) -> bool:
        """
        Envía un email usando Gmail SMTP.
        
        Args:
            to_email: Email del destinatario
            subject: Asunto del email
            html_content: Contenido HTML del email
            plain_content: Contenido en texto plano (fallback)
            
        Returns:
            True si se envió exitosamente, False en caso contrario
        """
        try:
            # Crear mensaje
            msg = MIMEMultipart('alternative')
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            msg['Subject'] = subject
            
            # Agregar contenido en texto plano (fallback)
            if plain_content:
                part1 = MIMEText(plain_content, 'plain', 'utf-8')
                msg.attach(part1)
            
            # Agregar contenido HTML
            part2 = MIMEText(html_content, 'html', 'utf-8')
            msg.attach(part2)
            
            # Conectar y enviar
            with smtplib.SMTP(self.smtp_host, self.smtp_port) as server:
                server.starttls()  # Habilitar TLS
                server.login(self.smtp_user, self.smtp_password)
                server.send_message(msg)
            
            logger.info(f"✅ Email enviado exitosamente a {to_email}")
            return True
            
        except smtplib.SMTPAuthenticationError:
            logger.error(f"❌ Error de autenticación SMTP. Verifica tu email y App Password.")
            return False
        except smtplib.SMTPException as e:
            logger.error(f"❌ Error SMTP enviando email a {to_email}: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"❌ Error inesperado enviando email a {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(
        self,
        to_email: str,
        nombre: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Envía email de bienvenida a un nuevo usuario.
        
        Args:
            to_email: Email del usuario
            nombre: Nombre del usuario
            metadata: Datos adicionales (ej: verification_token)
            
        Returns:
            True si se envió exitosamente
        """
        subject = "¡Bienvenido a RIM! 🏍️"
        
        # Contenido HTML (usando la plantilla)
        html_content = self._get_welcome_email_template(nombre, metadata)
        
        # Contenido en texto plano (fallback)
        plain_content = f"""
        ¡Hola {nombre}!
        
        Bienvenido a RIM - Sistema Inteligente de Moto.
        
        Tu cuenta ha sido creada exitosamente. Ahora puedes disfrutar de todas las funciones de nuestra plataforma:
        
        - Monitoreo en tiempo real de tu moto
        - Detección inteligente de fallas
        - Mantenimiento predictivo con IA
        - Chatbot asistente 24/7
        
        ¡Gracias por unirte a RIM!
        
        Saludos,
        El equipo de RIM
        """
        
        return self.send_email(to_email, subject, html_content, plain_content)
    
    def _get_welcome_email_template(
        self,
        nombre: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> str:
        """Retorna la plantilla HTML del email de bienvenida."""
        # Importar la plantilla
        from .email_templates import get_welcome_email_html
        return get_welcome_email_html(nombre, metadata)


# Instancia global del servicio de email
# IMPORTANTE: Configurar con tus credenciales de Gmail
email_service = EmailService(
    smtp_user="jenniferpalacin02@gmail.com",  # ← CAMBIAR AQUÍ
    smtp_password="zcuv nvzu tcxt fbbv",  # ← CAMBIAR AQUÍ (App Password de Gmail)
    from_email="jenniferpalacin02@gmail.com",  # ← CAMBIAR AQUÍ
    from_name="RIM - Sistema Inteligente de Moto"
)
