from django.core.exceptions import ValidationError
from django.core.validators import validate_email
from django.contrib.auth.hashers import make_password, check_password
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Users
from django.utils import timezone
from django.db.models import Sum

from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import permission_classes
from rest_framework_simplejwt.authentication import JWTAuthentication

from backend_TT.services import sendEmail, random_password
from Tasks.models import Task


@api_view(['POST'])
def register(request):
    try:
        data = request.data

        # Validación de campos obligatorios
        required_fields = ['username', 'email', 'password']
        for field in required_fields:
            if field not in data:
                return Response({'error': f'The field {field} is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validación del correo electrónico
        try:
            validate_email(data['email'])
        except ValidationError:
            return Response({'error': 'Invalid email address.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar si el correo electrónico o el nombre de usuario ya están en uso
        if Users.objects.filter(email=data['email']).exists():
            return Response({'error': 'El correo ya esta en uso.'}, status=status.HTTP_400_BAD_REQUEST)
        
        if Users.objects.filter(username=data['username']).exists():
            return Response({'error': 'El username ya esta en uso.'}, status=status.HTTP_400_BAD_REQUEST)

        # Obtener el campo opcional FullName
        full_name = data.get('full_name', 'Unknown FullName')  # Default si no se proporciona

        # Crear el nuevo usuario con fecha actual para effective_date
        new_user = Users(
            username=data['username'],
            email=data['email'],
            password=make_password(data['password']),
            full_name=full_name,
            effective_date=timezone.now()  # Fecha actual
        )
        new_user.save()

        return Response({
            'message': 'Registration successful!',
        }, status=status.HTTP_201_CREATED)

    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
def login(request):
    try:
        data = request.data
        email = data.get("email")
        password = data.get("password")

        if not email or not password:
            return Response({'error': 'Email and password are required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Verificar las credenciales del usuario
        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        if not check_password(password, user.password):
            return Response({'error': 'Invalid email or password.'}, status=status.HTTP_401_UNAUTHORIZED)

        user.last_login_date = timezone.now()
        user.save() 

        # Generar los tokens JWT
        refresh = RefreshToken.for_user(user)
        access_token = str(refresh.access_token)
        refresh_token = str(refresh)

        return Response({
            'message': 'Login successful',
            'access_token': access_token,
            'refresh_token': refresh_token
        }, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'An error occurred: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])  # El usuario debe estar autenticado
def recover_password(request):
    # Obtenemos el usuario autenticado a través del token JWT
    user = request.user
    
    # Generar nueva contraseña aleatoria
    new_password = random_password(6)
    user.set_password(new_password)  # Cambiar la contraseña del usuario
    user.save()  # Guardar los cambios en la base de datos

    # Enviar correo electrónico con la nueva contraseña
    type_email = "recover_password"
    sendEmail(user.email, type_email, new_password)

    return Response({'mensaje': 'Se ha enviado con éxito una nueva contraseña a su correo.'}, status=status.HTTP_200_OK)

@api_view(['POST'])
def reset_password(request):
    # Obtener datos del cuerpo de la solicitud
    email = request.data.get("email")
    new_password = request.data.get("new_password")
    confirm_password = request.data.get("confirm_password")
    
    # Verificar si el usuario existe en la base de datos con el correo proporcionado
    try:
        user = Users.objects.get(email=email)
    except Users.DoesNotExist:
        return Response({'error': 'No se encontró un usuario con ese correo electrónico.'},
                        status=status.HTTP_404_NOT_FOUND)

    # Verificar que las contraseñas coincidan
    if new_password != confirm_password:
        return Response({'error': 'Las contraseñas no coinciden.'},
                        status=status.HTTP_400_BAD_REQUEST)

    # Cambiar la contraseña del usuario
    user.set_password(new_password)
    user.save()  # Guardar los cambios en la base de datos

    return Response({'mensaje': 'La contraseña ha sido restablecida exitosamente.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_info(request):
    # Obtenemos el usuario autenticado a través del token JWT
    user = request.user

    # Obtenemos todas las tareas del usuario
    tasks = Task.objects.filter(usuario=user)

    # Sumamos los puntos de las tareas agrupados por beca (ActivityID)
    beca_points = tasks.values('actividad__beca__nombre').annotate(total_points=Sum('puntos'))

    # Creamos el diccionario para devolver en la respuesta
    beca_points_dict = {item['actividad__beca__nombre']: item['total_points'] for item in beca_points}

    # Datos del usuario
    user_data = {
        'username': user.username,
        'email': user.email,
        'full_name': user.full_name,
        'last_login_date': user.last_login_date,
        'beca_points': beca_points_dict  # Agregamos los puntos totales por beca
    }

    # Devolver los datos del usuario en la respuesta
    return Response(user_data, status=status.HTTP_200_OK)
