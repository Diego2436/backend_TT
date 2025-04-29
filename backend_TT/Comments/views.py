from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from .models import Comment
from Authentication.models import Users
from django.contrib.auth import get_user_model


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_comment(request):
    try:
        # Obtener el usuario autenticado desde el token JWT
        user = request.user

        # Obtener el comentario desde el cuerpo de la solicitud
        descripcion = request.data.get('comentario')  # o 'descripcion'

        # Validar que el comentario no esté vacío
        if not descripcion:
            return Response({'error': 'El comentario es requerido.'}, status=status.HTTP_400_BAD_REQUEST)

        # Crear el nuevo comentario
        nuevo_comentario = Comment.objects.create(
            usuario=user,  # Asigna el usuario autenticado obtenido del token
            descripcion=descripcion
        )

        # Retornar la información del comentario creado
        return Response({
            'id': nuevo_comentario.id,
            'usuario': user.username,  # El nombre de usuario del token
            'descripcion': nuevo_comentario.descripcion,
            'created': nuevo_comentario.created,
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al crear el comentario: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_all_comments(request):
    try:
        # Obtener todos los comentarios con el usuario asociado
        comentarios = Comment.objects.select_related('usuario').all()

        # Construir la respuesta en formato JSON
        comentarios_data = [
            {
                'id': comentario.id,
                'usuario': comentario.usuario.username,
                'descripcion': comentario.descripcion,
                'created': comentario.created,
            } for comentario in comentarios
        ]

        return Response(comentarios_data, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al obtener los comentarios: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
