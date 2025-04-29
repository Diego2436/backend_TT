from django.shortcuts import render
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Task
from Beca.models import ActividadBeca
from django.conf import settings
import boto3
from Files.models import VerificationFile
from django.db.models import Q
from datetime import datetime
from backend_TT.services import *

# S3 client using boto3
s3_client = boto3.client(
    's3',
    aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
    aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
    region_name=settings.AWS_S3_REGION_NAME
)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_tasks(request):
    try:
        # Obtener el user_id desde el token JWT
        user_id = request.user.id

        # Filtrar tareas que pertenezcan al usuario autenticado
        tareas = Task.objects.filter(usuario_id=user_id)

        # Crear la lista de tareas con los campos específicos solicitados
        tareas_list = [
            {
                'id': tarea.id,
                'fecha_vencimiento': tarea.fecha_vencimiento.strftime('%d-%m-%Y'),
                'estado': tarea.estado,
            }
            for tarea in tareas
        ]

        # Retornar la lista de tareas en formato JSON
        return Response(tareas_list, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

  
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_user_tasks(request):
    """Endpoint to get all tasks for the authenticated user."""
    try:
        # Obtener el user_id del usuario autenticado
        user_id = request.user.id

        # Filtrar todas las tareas que pertenezcan al usuario autenticado
        tareas = Task.objects.filter(usuario_id=user_id)

        # Crear una lista con todos los datos de cada tarea
        tareas_list = [
            {
                'id': tarea.id,
                'fecha_vencimiento': tarea.fecha_vencimiento.strftime('%d-%m-%Y'),
                'descripcion': tarea.descripcion,
                'estado': tarea.estado,
                'puntos': tarea.puntos,
                'actividad_id': tarea.actividad.id,
                'usuario_id': tarea.usuario.id,
            }
            for tarea in tareas
        ]

        # Retornar la lista de tareas en formato JSON
        return Response(tareas_list, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_task(request):
    """Endpoint to create a new task for the authenticated user."""
    try:
        user_id = request.user.id
        actividad_id = request.data.get('actividad_id')
        descripcion = request.data.get('descripcion')
        fecha_vencimiento = request.data.get('fecha_vencimiento')
        puntos = request.data.get('puntos', 0)

        actividad = ActividadBeca.objects.filter(id=actividad_id).first()
        if not actividad:
            return Response({'error': 'La actividad especificada no existe.'}, status=status.HTTP_400_BAD_REQUEST)

        fecha_vencimiento_date = datetime.strptime(fecha_vencimiento, "%Y-%m-%d").date()

        tarea_existente_actividad = Task.objects.filter(actividad_id=actividad_id, usuario_id=user_id).exists()
        if tarea_existente_actividad:
            return Response({'error': 'Ya existe una tarea para esta actividad para este usuario.'}, status=status.HTTP_400_BAD_REQUEST)

        tarea_existente_fecha = Task.objects.filter(usuario_id=user_id, fecha_vencimiento=fecha_vencimiento_date).exists()
        if tarea_existente_fecha:
            return Response({'error': 'Ya existe una tarea para este usuario en esta fecha.'}, status=status.HTTP_400_BAD_REQUEST)

        nueva_tarea = Task.objects.create(
            fecha_vencimiento=fecha_vencimiento_date,
            descripcion=descripcion,
            estado='en progreso',
            puntos=puntos,
            actividad=actividad,
            usuario_id=user_id
        )

        # Enviar correo
        usuario_email = request.user.email
        send_task_notification(
            email=usuario_email,
            actividad_nombre=actividad.nombre,
            descripcion=descripcion,
            fecha_vencimiento=fecha_vencimiento_date
        )

        return Response({
            'id': nueva_tarea.id,
            'fecha_vencimiento': nueva_tarea.fecha_vencimiento,
            'descripcion': nueva_tarea.descripcion,
            'estado': nueva_tarea.estado,
            'puntos': nueva_tarea.puntos,
            'actividad_id': nueva_tarea.actividad.id,
            'usuario_id': nueva_tarea.usuario.id,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['DELETE'])
@permission_classes([IsAuthenticated])
def delete_task_with_files(request, task_id):
    user = request.user  # Obtener el usuario autenticado

    try:
        # Recuperar la tarea a eliminar
        task_to_delete = Task.objects.get(id=task_id)

        # Verificar que la tarea pertenece al usuario autenticado
        if task_to_delete.usuario != user:
            return Response({"error": "No tienes permiso para eliminar esta tarea."}, status=status.HTTP_403_FORBIDDEN)

        # Eliminar los archivos asociados en S3 y de la base de datos, junto con sus verificaciones
        for file in task_to_delete.files.all():
            # Eliminar el archivo de verificación relacionado si existe
            VerificationFile.objects.filter(file=file).delete()

            # Obtener el nombre del archivo en la ubicación S3
            s3_key = file.location.split('/')[-1]
            s3_path = f'pdfs/{user.username}/{s3_key}'

            # Eliminar el archivo del almacenamiento S3
            s3_client.delete_object(
                Bucket=settings.AWS_STORAGE_BUCKET_NAME,
                Key=s3_path
            )

            # Eliminar el archivo de la base de datos
            file.delete()

        # Finalmente, eliminar la tarea de la base de datos
        task_to_delete.delete()

        return Response({"message": "Tarea, archivos asociados y verificaciones eliminados exitosamente."}, status=status.HTTP_204_NO_CONTENT)

    except Task.DoesNotExist:
        return Response({"error": "Tarea no encontrada."}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_task_details(request, task_id):
    """Endpoint to get the details of a specific task."""
    try:
        # Obtener el usuario autenticado
        user_id = request.user.id

        # Validar que la tarea existe y pertenece al usuario
        tarea = Task.objects.filter(id=task_id, usuario_id=user_id).first()
        if not tarea:
            return Response({'error': 'La tarea especificada no existe o no tienes permiso para acceder a ella.'}, status=status.HTTP_404_NOT_FOUND)

        # Retornar los detalles de la tarea
        return Response({
            'id': tarea.id,
            'fecha_vencimiento': tarea.fecha_vencimiento,
            'descripcion': tarea.descripcion,
            'estado': tarea.estado,
            'puntos': tarea.puntos,
            'actividad_id': tarea.actividad.id,
            'usuario_id': tarea.usuario.id,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_task(request, task_id):
    """Endpoint to update an existing task."""
    try:
        user_id = request.user.id
        tarea = Task.objects.filter(id=task_id, usuario_id=user_id).first()
        if not tarea:
            return Response({'error': 'La tarea especificada no existe o no tienes permiso para modificarla.'}, status=status.HTTP_404_NOT_FOUND)

        fecha_vencimiento = request.data.get('fecha_vencimiento')
        descripcion = request.data.get('descripcion')
        puntos = request.data.get('puntos')
        actividad_id = request.data.get('actividad_id')

        if actividad_id and actividad_id != tarea.actividad.id:
            actividad = ActividadBeca.objects.filter(id=actividad_id).first()
            if not actividad:
                return Response({'error': 'La actividad especificada no existe.'}, status=status.HTTP_400_BAD_REQUEST)
            if Task.objects.filter(actividad_id=actividad_id, usuario_id=user_id).exclude(id=task_id).exists():
                return Response({'error': 'Ya existe una tarea para esta actividad para este usuario.'}, status=status.HTTP_400_BAD_REQUEST)
            tarea.actividad = actividad

        if fecha_vencimiento:
            fecha_vencimiento_date = datetime.strptime(fecha_vencimiento, "%Y-%m-%d").date()
            if Task.objects.filter(usuario_id=user_id, fecha_vencimiento=fecha_vencimiento_date).exclude(id=task_id).exists():
                return Response({'error': 'Ya existe una tarea para este usuario en esta fecha.'}, status=status.HTTP_400_BAD_REQUEST)
            tarea.fecha_vencimiento = fecha_vencimiento_date

        if descripcion:
            tarea.descripcion = descripcion
        if puntos is not None:
            tarea.puntos = puntos

        tarea.save()

        # Enviar correo
        usuario_email = request.user.email
        send_task_notification(
            email=usuario_email,
            actividad_nombre=tarea.actividad.nombre,
            descripcion=tarea.descripcion,
            fecha_vencimiento=tarea.fecha_vencimiento
        )

        return Response({
            'id': tarea.id,
            'fecha_vencimiento': tarea.fecha_vencimiento,
            'descripcion': tarea.descripcion,
            'estado': tarea.estado,
            'puntos': tarea.puntos,
            'actividad_id': tarea.actividad.id,
            'usuario_id': tarea.usuario.id,
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tasks_edd(request):
    """
    Endpoint para obtener todas las tareas de la beca EDD (id=1) para el usuario autenticado.
    """
    try:
        # Obtener el user_id del usuario autenticado
        user_id = request.user.id

        # Filtrar las actividades asociadas a la beca EDD (id=1)
        actividades_edd = ActividadBeca.objects.filter(beca_id=1)

        # Filtrar las tareas relacionadas con esas actividades y el usuario autenticado
        tareas = Task.objects.filter(actividad__in=actividades_edd, usuario_id=user_id)

        # Verificar si existen tareas para el usuario
        if not tareas.exists():
            return Response(
                {'message': 'No se encontraron tareas para el usuario en la beca EDD'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear la lista de tareas
        tareas_list = [
            {
                'id': tarea.id,
                'fecha_vencimiento': tarea.fecha_vencimiento.strftime('%d-%m-%Y'),
                'descripcion': tarea.descripcion,
                'estado': tarea.estado,
                'puntos': tarea.puntos,
                'actividad_id': tarea.actividad.id,
                'usuario_id': tarea.usuario.id,
            }
            for tarea in tareas
        ]

        return Response(tareas_list, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_tasks_edi(request):
    """
    Endpoint para obtener todas las tareas de la beca EDI (id=2) para el usuario autenticado.
    """
    try:
        # Obtener el user_id del usuario autenticado
        user_id = request.user.id

        # Filtrar las actividades asociadas a la beca EDI (id=2)
        actividades_edi = ActividadBeca.objects.filter(beca_id=2)

        # Filtrar las tareas relacionadas con esas actividades y el usuario autenticado
        tareas = Task.objects.filter(actividad__in=actividades_edi, usuario_id=user_id)

        # Verificar si existen tareas para el usuario
        if not tareas.exists():
            return Response(
                {'message': 'No se encontraron tareas para el usuario en la beca EDI'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Crear la lista de tareas
        tareas_list = [
            {
                'id': tarea.id,
                'fecha_vencimiento': tarea.fecha_vencimiento.strftime('%d-%m-%Y'),
                'descripcion': tarea.descripcion,
                'estado': tarea.estado,
                'puntos': tarea.puntos,
                'actividad_id': tarea.actividad.id,
                'usuario_id': tarea.usuario.id,
            }
            for tarea in tareas
        ]

        return Response(tareas_list, status=status.HTTP_200_OK)

    except Exception as e:
        return Response(
            {'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )