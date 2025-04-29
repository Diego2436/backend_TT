from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status
from .models import Beca, ActividadBeca

@api_view(['GET'])
def list_becas(request):
    """Endpoint to get all scholarships"""
    try:
        # Retrieve all available scholarships
        becas = Beca.objects.all()

        # Create a list of dictionaries with scholarship information
        becas_list = [
            {
                'id': beca.id,
                'name': beca.nombre,
                'description': beca.descripcion
            } 
            for beca in becas
        ]

        # Return the response in JSON format
        response = {'scholarships': becas_list}
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def get_activities_edd(request):
    try:
        # Fetch the scholarship with ID = 1
        beca = Beca.objects.filter(id=1).first()

        if not beca:
            return Response({'error': 'La beca con ID 1 no existe.'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve activities related to the scholarship with ID = 1
        actividades = ActividadBeca.objects.filter(beca=beca)

        # Create a list of dictionaries with numbered activity information
        actividades_list = [
            {
                'ID': actividad.id,
                'Nombre': actividad.nombre,
                'Codigo': actividad.codigo,
            }
            for idx, actividad in enumerate(actividades)
        ]

        # Return the response in JSON format
        response = {
            'Nombre de la Beca': beca.nombre,
            'Actividades': actividades_list
        }
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def get_activities_edi(request):
    """Endpoint to get activities for the scholarship with ID = 2 (EDI)"""
    try:
        # Fetch the scholarship with ID = 2
        beca = Beca.objects.filter(id=2).first()

        if not beca:
            return Response({'error': 'La beca con ID 2 no existe.'}, status=status.HTTP_404_NOT_FOUND)

        # Retrieve activities related to the scholarship with ID = 2
        actividades = ActividadBeca.objects.filter(beca=beca)

        # Create a list of dictionaries with numbered activity information
        actividades_list = [
            {
                'ID': actividad.id,
                'Nombre': actividad.nombre,
                'Codigo': actividad.codigo,
            }
            for idx, actividad in enumerate(actividades)
        ]

        # Return the response in JSON format
        response = {
            'Nombre de la Beca': beca.nombre,
            'Actividades': actividades_list
        }
        return Response(response, status=status.HTTP_200_OK)

    except Exception as e:
        return Response({'error': f'Ocurrió un error al procesar la solicitud: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)