"""
Plantillas HTML para emails.
"""
from typing import Optional, Dict, Any


def get_welcome_email_html(nombre: str, metadata: Optional[Dict[str, Any]] = None) -> str:
    """
    Retorna el HTML del email de bienvenida.
    
    Args:
        nombre: Nombre del usuario
        metadata: Datos adicionales (ej: verification_token)
    """
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Bienvenido a RIM</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%); padding: 40px 20px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: bold;">
                                🏍️ RIM
                            </h1>
                            <p style="color: #ffffff; margin: 10px 0 0 0; font-size: 16px; opacity: 0.9;">
                                Sistema Inteligente de Moto
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <h2 style="color: #333333; margin: 0 0 20px 0; font-size: 24px;">
                                ¡Hola {nombre}! 👋
                            </h2>
                            
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Bienvenido a <strong>RIM - Sistema Inteligente de Moto</strong>. Tu cuenta ha sido creada exitosamente.
                            </p>
                            
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 30px 0;">
                                Ahora puedes disfrutar de todas las funciones de nuestra plataforma:
                            </p>
                            
                            <!-- Features -->
                            <table width="100%" cellpadding="0" cellspacing="0" style="margin-bottom: 30px;">
                                <tr>
                                    <td style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #FF6B00; margin-bottom: 10px;">
                                        <strong style="color: #333333; font-size: 16px;">📊 Monitoreo en Tiempo Real</strong>
                                        <p style="color: #666666; font-size: 14px; margin: 5px 0 0 0;">
                                            Visualiza el estado de tu moto en tiempo real
                                        </p>
                                    </td>
                                </tr>
                                <tr><td style="height: 10px;"></td></tr>
                                <tr>
                                    <td style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #FF6B00;">
                                        <strong style="color: #333333; font-size: 16px;">🔧 Detección Inteligente de Fallas</strong>
                                        <p style="color: #666666; font-size: 14px; margin: 5px 0 0 0;">
                                            Identifica problemas antes de que se vuelvan críticos
                                        </p>
                                    </td>
                                </tr>
                                <tr><td style="height: 10px;"></td></tr>
                                <tr>
                                    <td style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #FF6B00;">
                                        <strong style="color: #333333; font-size: 16px;">🤖 Mantenimiento Predictivo con IA</strong>
                                        <p style="color: #666666; font-size: 14px; margin: 5px 0 0 0;">
                                            Recibe recomendaciones personalizadas de mantenimiento
                                        </p>
                                    </td>
                                </tr>
                                <tr><td style="height: 10px;"></td></tr>
                                <tr>
                                    <td style="padding: 15px; background-color: #f8f9fa; border-left: 4px solid #FF6B00;">
                                        <strong style="color: #333333; font-size: 16px;">💬 Chatbot Asistente 24/7</strong>
                                        <p style="color: #666666; font-size: 14px; margin: 5px 0 0 0;">
                                            Obtén ayuda instantánea cuando la necesites
                                        </p>
                                    </td>
                                </tr>
                            </table>
                            
                            <!-- CTA Button -->
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <a href="http://localhost:3000" style="display: inline-block; padding: 15px 40px; background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%); color: #ffffff; text-decoration: none; border-radius: 5px; font-size: 16px; font-weight: bold;">
                                            Ir a mi Dashboard
                                        </a>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                Si tienes alguna pregunta, no dudes en contactarnos.
                            </p>
                            
                            <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 10px 0 0 0;">
                                ¡Gracias por unirte a RIM! 🚀
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="color: #999999; font-size: 12px; margin: 0 0 10px 0;">
                                © 2025 RIM - Sistema Inteligente de Moto. Todos los derechos reservados.
                            </p>
                            <p style="color: #999999; font-size: 12px; margin: 0;">
                                Este es un email automático, por favor no respondas a este mensaje.
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """


def get_password_reset_email_html(reset_token: str) -> str:
    """Plantilla para email de recuperación de contraseña."""
    return f"""
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Recuperar Contraseña</title>
</head>
<body style="margin: 0; padding: 0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f4f4;">
    <table width="100%" cellpadding="0" cellspacing="0" style="background-color: #f4f4f4; padding: 20px;">
        <tr>
            <td align="center">
                <table width="600" cellpadding="0" cellspacing="0" style="background-color: #ffffff; border-radius: 10px; overflow: hidden; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                    
                    <!-- Header -->
                    <tr>
                        <td style="background: linear-gradient(135deg, #FF6B00 0%, #FF8C00 100%); padding: 40px 20px; text-align: center;">
                            <h1 style="color: #ffffff; margin: 0; font-size: 32px; font-weight: bold;">
                                🔐 Recuperar Contraseña
                            </h1>
                        </td>
                    </tr>
                    
                    <!-- Body -->
                    <tr>
                        <td style="padding: 40px 30px;">
                            <p style="color: #666666; font-size: 16px; line-height: 1.6; margin: 0 0 20px 0;">
                                Has solicitado recuperar tu contraseña. Usa el siguiente código para restablecer tu contraseña:
                            </p>
                            
                            <table width="100%" cellpadding="0" cellspacing="0">
                                <tr>
                                    <td align="center" style="padding: 20px 0;">
                                        <div style="display: inline-block; padding: 20px 40px; background-color: #f8f9fa; border: 2px dashed #FF6B00; border-radius: 5px; font-size: 24px; font-weight: bold; color: #333333; letter-spacing: 2px;">
                                            {reset_token}
                                        </div>
                                    </td>
                                </tr>
                            </table>
                            
                            <p style="color: #999999; font-size: 14px; line-height: 1.6; margin: 20px 0 0 0; text-align: center;">
                                Este código expira en 1 hora.
                            </p>
                            
                            <p style="color: #666666; font-size: 14px; line-height: 1.6; margin: 30px 0 0 0;">
                                Si no solicitaste este cambio, ignora este email.
                            </p>
                        </td>
                    </tr>
                    
                    <!-- Footer -->
                    <tr>
                        <td style="background-color: #f8f9fa; padding: 30px; text-align: center; border-top: 1px solid #e0e0e0;">
                            <p style="color: #999999; font-size: 12px; margin: 0;">
                                © 2025 RIM - Sistema Inteligente de Moto
                            </p>
                        </td>
                    </tr>
                    
                </table>
            </td>
        </tr>
    </table>
</body>
</html>
    """
