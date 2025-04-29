import smtplib, secrets, string
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

def sendEmail(email, type, token_or_password=None):
    # Configuración del servidor SMTP
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'marvel2436@gmail.com'
    smtp_password = 'ymdkpbvfkdsgylre'

    # Direcciones de correo (puedes enviar a múltiples destinatarios separándolos por comas)
    from_email = 'marvel2436@gmail.com'
    to_email = email

    # Configuración del mensaje
    if type == "register":
        subject = 'Verificación de la cuenta'
        body = f"Entra al siguiente enlace para verificar la cuenta: http://127.0.0.1:8000/api/docente/verificar/?token={token_or_password}"
    elif type == "recover_password":
        subject = 'Recuperar contraseña'
        body = f"Tu nueva contraseña es: {token_or_password}"
    else:
        raise ValueError(f"Tipo de correo no soportado: {type}")

    # Construir el mensaje
    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    # Conectar al servidor SMTP y enviar el correo
    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, message.as_string())
        print("Correo enviado exitosamente.")
    except Exception as e:
        print(f"No se pudo enviar el correo. Error: {e}")

def random_password(longitud=6):
    caracteres = string.ascii_letters + string.digits  # letras y dígitos
    contrasena_plana = ''.join(secrets.choice(caracteres) for _ in range(longitud))
    return contrasena_plana

def send_task_notification(email, actividad_nombre, descripcion, fecha_vencimiento):
    """
    Envía un correo de notificación relacionado con tareas.
    
    :param email: Dirección de correo del usuario.
    :param actividad_nombre: Nombre de la actividad asociada a la tarea.
    :param descripcion: Descripción de la tarea.
    :param fecha_vencimiento: Fecha de vencimiento de la tarea.
    """
    smtp_server = 'smtp.gmail.com'
    smtp_port = 587
    smtp_username = 'marvel2436@gmail.com'
    smtp_password = 'ymdkpbvfkdsgylre'

    from_email = 'marvel2436@gmail.com'
    to_email = email

    subject = 'Notificación de tarea'
    body = (f"Detalles de la tarea:\n\n"
            f"Actividad: {actividad_nombre}\n"
            f"Descripción: {descripcion}\n"
            f"Fecha de vencimiento: {fecha_vencimiento}\n")

    message = MIMEMultipart()
    message['From'] = from_email
    message['To'] = to_email
    message['Subject'] = subject
    message.attach(MIMEText(body, 'plain'))

    try:
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            server.starttls()
            server.login(smtp_username, smtp_password)
            server.sendmail(from_email, to_email, message.as_string())
        print("Correo de tarea enviado exitosamente.")
    except Exception as e:
        print(f"No se pudo enviar el correo de tarea. Error: {e}")
