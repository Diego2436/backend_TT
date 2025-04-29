from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Prefetch
from botocore.exceptions import ClientError
import boto3
from .models import *
from Tasks.models import Task
from Beca.models import ActividadVerificacion

# S3 client using boto3
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)


@api_view(['POST'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def upload_pdf(request, task_id):  # task_id is now a URL parameter
    if 'file' not in request.FILES:
        return Response({"error": "No file provided."}, status=status.HTTP_400_BAD_REQUEST)

    file = request.FILES['file']

    # Check that the file is a PDF
    if not file.name.endswith('.pdf'):
        return Response({"error": "Only PDF files are allowed."}, status=status.HTTP_400_BAD_REQUEST)

    # Get the authenticated user
    user = request.user

    try:
        # Validate that the task exists and is associated with the user
        task = Task.objects.get(id=task_id, usuario=user)
    except Task.DoesNotExist:
        return Response({"error": "Task not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)

    # Create the folder with the username for S3
    username = user.username
    base_filename, file_extension = file.name.rsplit('.', 1)
    s3_filename = f'pdfs/{username}/{file.name}'

    # Check if a file with the same name already exists in S3
    existing_files = []
    try:
        # List existing files in the user's folder in S3
        existing_files = s3_client.list_objects_v2(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Prefix=f'pdfs/{username}/'
        ).get('Contents', [])
    except Exception as e:
        return Response({"error": f"Error checking existing files: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Check if the file already exists and generate a new name if necessary
    count = 1
    while any(obj['Key'] == s3_filename for obj in existing_files):
        s3_filename = f'pdfs/{username}/{base_filename}_{count}.{file_extension}'
        count += 1

    try:
        # Upload the file to S3 in the user's folder
        s3_client.upload_fileobj(
            file,
            settings.AWS_STORAGE_BUCKET_NAME,
            s3_filename
        )

        # Save the reference in the database
        file_model = File.objects.create(
            name=s3_filename.split('/')[-1],  # Save only the file name (not the full path)
            location=f'https://{settings.AWS_STORAGE_BUCKET_NAME}.s3.amazonaws.com/{s3_filename}',
            task=task  # Associate the file with the task
        )

        return Response({
            "message": "File uploaded successfully.",
            "file": {
                "name": file_model.name,
                "location": file_model.location
            }
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({"error": f"An error occurred while uploading the file: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def get_files_for_task(request, task_id):  # task_id is a URL parameter
    user = request.user  # Get the authenticated user

    try:
        # Validate that the task exists and is associated with the user
        task = Task.objects.get(id=task_id, usuario=user)

        # Retrieve files associated with the task
        files = task.files.all()  # Accessing related files using the related name 'files'

        # Prepare response data
        file_data = [{
            'id': file.id,
            'name': file.name,
            'location': file.location
        } for file in files]

        due_date_formatted = task.fecha_vencimiento.strftime('%d/%m/%Y')

        actividad_beca_data = {
            'id': task.actividad.id,
            'nombre_actividad': task.actividad.nombre,
            'nombre_beca': task.actividad.beca.nombre
        } if task.actividad else None

        return Response({
            "task_id": task_id,
            "due_date": due_date_formatted,
            "actividad_beca": actividad_beca_data,
            "files": file_data
        }, status=status.HTTP_200_OK)

    except Task.DoesNotExist:
        return Response({"error": "Task not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Asegura que el usuario esté autenticado
def get_files_with_status(request, task_id):
    user = request.user  # Obtener el usuario autenticado

    try:
        # Verifica que la tarea existe y está asociada al usuario
        task = Task.objects.get(id=task_id, usuario=user)

        # Prefetch para optimizar la relación entre File y VerificationFile
        files = File.objects.filter(task=task).select_related('verificationfile')

        # Construye la respuesta con los datos necesarios
        file_data = []
        for file in files:
            file_info = {
                'id': file.id,
                'name': file.name,
                'location': file.location,
                'file_status': file.verificationfile.file_status if hasattr(file, 'verificationfile') else None
            }
            file_data.append(file_info)

        due_date_formatted = task.fecha_vencimiento.strftime('%d/%m/%Y')

        actividad_beca_data = {
            'id': task.actividad.id,
            'nombre_actividad': task.actividad.nombre,
            'nombre_beca': task.actividad.beca.nombre
        } if task.actividad else None

        return Response({
            "task_id": task_id,
            "due_date": due_date_formatted,
            "actividad_beca": actividad_beca_data,
            "files": file_data
        }, status=status.HTTP_200_OK)

    except Task.DoesNotExist:
        return Response({"error": "Task not found or not associated with the user."}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def get_all_user_activities_files(request):
    user = request.user  # Get the authenticated user

    # Retrieve all tasks associated with the user
    tasks = Task.objects.filter(usuario=user)

    # Prepare a list to hold all tasks and their associated file names
    task_data = []

    # Loop through each task and get its associated files
    for task in tasks:
        task_files = task.files.all()  # Retrieve the files for this task

        # If there are files, get their names
        file_names = [file.name for file in task_files]

        due_date_formatted = task.fecha_vencimiento.strftime('%d/%m/%Y')

        actividad_beca_data = {
            'id': task.actividad.id,
            'nombre_actividad': task.actividad.nombre,
            'nombre_beca': task.actividad.beca.nombre
        } if task.actividad else None

        # Append the task data with the file names
        task_data.append({
            'task_id': task.id,
            'due_date': due_date_formatted,
            'actividad_beca': actividad_beca_data,
            'pdf': file_names  # List of file names
        })

    return Response({
        "user_id": user.id,
        "tasks": task_data
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # Solo usuarios autenticados pueden acceder
def view_pdf(request, file_id):
    user = request.user  # Obtener el usuario autenticado

    try:
        # Buscar el archivo en la base de datos
        file_to_view = File.objects.get(id=file_id)

        # Verificar que el archivo pertenezca al usuario autenticado
        if file_to_view.task.usuario != user:
            return Response({"error": "No tienes permiso para ver este archivo."}, status=status.HTTP_403_FORBIDDEN)

        # Obtener la clave del archivo en S3
        s3_key = file_to_view.location.split('.com/')[-1]  # Extraer la clave desde la URL completa en S3

        # Generar una URL temporal firmada (pre-signed URL) para acceder al archivo
        try:
            s3_presigned_url = s3_client.generate_presigned_url(
                'get_object',
                Params={
                    'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                    'Key': s3_key
                },
                ExpiresIn=3600  # La URL expira en 1 hora
            )
        except ClientError as e:
            return Response({"error": f"Error al generar la URL: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Retornar la URL para que el cliente pueda acceder al archivo
        return Response({
            "message": "URL generada exitosamente.",
            "pdf_url": s3_presigned_url
        }, status=status.HTTP_200_OK)

    except File.DoesNotExist:
        return Response({"error": "Archivo no encontrado."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])  # Ensure the user is authenticated
def delete_file(request, file_id):
    user = request.user  # Get the authenticated user

    try:
        # Retrieve the file record from the database
        file_to_delete = File.objects.get(id=file_id)

        # Verify that the file belongs to the authenticated user (if needed)
        if file_to_delete.task.usuario != user:
            return Response({"error": "You do not have permission to delete this file."}, status=status.HTTP_403_FORBIDDEN)

        # Construct the S3 key for the file to be deleted
        s3_key = file_to_delete.location.split('/')[-1]  # Get the file name from the location
        s3_path = f'pdfs/{user.username}/{s3_key}'  # Construct the S3 path

        # Delete the file from S3
        s3_client.delete_object(
            Bucket=settings.AWS_STORAGE_BUCKET_NAME,
            Key=s3_path
        )

        # Delete the file record from the database
        file_to_delete.delete()

        return Response({"message": "File deleted successfully."}, status=status.HTTP_204_NO_CONTENT)

    except File.DoesNotExist:
        return Response({"error": "File not found."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_files_with_actividad_verificacion(request):
    # Obtener el user_id del JWT
    user_id = request.user.id

    # Obtener todos los archivos (File) que están relacionados con alguna tarea (Task)
    # cuyo usuario es el user_id obtenido del JWT
    files = File.objects.filter(task__usuario_id=user_id)

    # Crear una lista para almacenar los resultados
    data = []

    # Recorrer cada archivo y obtener las ActividadVerificacion relacionadas
    for file in files:
        actividad_verificaciones = ActividadVerificacion.objects.filter(
            actividadBeca=file.task.actividad
        )
        
        # Construir la estructura de respuesta para cada archivo
        file_data = {
            "id": file.id,
            "name": file.name,
            "location": file.location,
            "actividad_verificaciones": [
                {
                    "actividadBeca": actividad_verificacion.actividadBeca_id,
                    "verificacion": actividad_verificacion.verificacion_id
                }
                for actividad_verificacion in actividad_verificaciones
            ]
        }
        
        # Añadir el archivo con sus relaciones a la lista de datos
        data.append(file_data)

    # Retornar la respuesta JSON con la estructura deseada
    return Response(data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verificaciones_by_file(request, file_id):
    # Obtener el archivo específico usando el file_id de la URL y el usuario autenticado
    file = get_object_or_404(File, id=file_id, task__usuario=request.user)

    # Obtener todas las instancias de ActividadVerificacion relacionadas con la actividad de la tarea del archivo
    actividad_verificaciones = ActividadVerificacion.objects.filter(
        actividadBeca=file.task.actividad
    )

    # Construir la respuesta con solo el nombre y descripción de cada verificación
    verificaciones_data = [
        {
            "id": actividad_verificacion.verificacion.id,
            "nombre": actividad_verificacion.verificacion.name,
            "descripcion": actividad_verificacion.verificacion.description
        }
        for actividad_verificacion in actividad_verificaciones
    ]

    # Retornar la respuesta con la lista de verificaciones
    return Response(verificaciones_data, status=200)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def update_verificaciones_by_file(request, file_id):
    # Obtener el archivo y verificar que pertenece al usuario autenticado
    file = get_object_or_404(File, id=file_id, task__usuario=request.user)
    
    # Obtener la actividad relacionada con el archivo (actividad_beca)
    actividad_beca = file.task.actividad
    
    # Obtener todas las verificaciones asociadas con la actividad
    actividad_verificaciones = ActividadVerificacion.objects.filter(actividadBeca=actividad_beca)

    # Obtener las verificaciones enviadas en la petición
    verifications = request.data.get("verifications", [])

    # Obtener los IDs válidos de las verificaciones asociadas a la actividad
    valid_verification_ids = [actividad_verificacion.verificacion.id for actividad_verificacion in actividad_verificaciones]

    # Verificar si los IDs de la solicitud son válidos
    invalid_ids = [verification['id'] for verification in verifications if verification['id'] not in valid_verification_ids]

    if invalid_ids:
        return Response({"error": f"Los siguientes IDs no son válidos: {', '.join(map(str, invalid_ids))}"}, status=status.HTTP_400_BAD_REQUEST)

    # Contadores para el cálculo del estado del archivo
    verified_count = 0
    total_verifications = len(actividad_verificaciones)

    # Actualizar el conteo de verificaciones correctas
    for verification in verifications:
        if verification.get("is_verified"):
            verified_count += 1

    # Determinar el estado del archivo en base a los conteos
    if verified_count == total_verifications:
        file_status = "completada"
    elif verified_count == 0:
        file_status = "errores"
    else:
        file_status = "precaucion"

    # Crear o actualizar la entrada en VerificationFile
    verification_file, created = VerificationFile.objects.update_or_create(
        file=file,
        defaults={
            'file_status': file_status,
            'verified_count': verified_count,
            'total_verifications': total_verifications,
            'actividad_verificacion': actividad_verificaciones.first()  # Relacionar con la primera ActividadVerificacion
        }
    )

    # Actualizar el estado de la tarea asociada al archivo
    task = file.task  # Obtener la tarea asociada al archivo
    
    if task:
        print(f"Estado actual de la tarea: {task.estado}")
        
        if file_status == "completada":
            task.estado = "completada"
        elif file_status == "errores":
            task.estado = "errores"
        elif file_status == "precaucion":
            task.estado = "precaucion"
        
        task.save()  # Guardar los cambios en la tarea
        task.refresh_from_db()  # Recargar la tarea desde la base de datos
        print(f"Nuevo estado de la tarea: {task.estado}")
    else:
        print("No se pudo encontrar la tarea asociada al archivo")

    # Retornar el resumen de estado
    return Response({
        "file_id": file.id,
        "file_status": file_status,
        "verified_count": verified_count,
        "total_verifications": total_verifications
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_verification_status_and_count(request, file_id):
    # Obtener el archivo de verificación relacionado con el file_id
    verification_file = get_object_or_404(VerificationFile, file__id=file_id)
    
    # Construir la respuesta con los campos Status y Count
    data = {
        "file_status": verification_file.file_status,
        "verified_count": verification_file.verified_count,
        "total_verifications": verification_file.total_verifications
    }
    
    # Retornar la respuesta con los datos
    return Response(data, status=200)
