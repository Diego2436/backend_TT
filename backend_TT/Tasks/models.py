from django.db import models
from Authentication.models  import Users
from Beca.models  import ActividadBeca

# Create your models here.
class Task(models.Model):
    fecha_vencimiento = models.DateField(db_column='DueDate')
    descripcion = models.TextField(db_column='Description')
    estado = models.CharField(max_length=255, db_column='Status', default='en progreso')
    puntos = models.IntegerField(db_column='Points')
    actividad = models.ForeignKey(ActividadBeca, on_delete=models.CASCADE, db_column='ActivityID')
    usuario = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserID')

    class Meta:
        db_table = 'Tasks' 