from django.db import models
from Tasks.models import Task
from Beca.models import ActividadVerificacion

class File(models.Model):
    name = models.CharField(max_length=255, db_column='Name') 
    location = models.CharField(max_length=500, db_column='Location') 
    task = models.ForeignKey(Task, on_delete=models.CASCADE, db_column='TaskID',related_name='files') 

    class Meta:
        db_table = 'Files'

class VerificationFile(models.Model):
    file = models.OneToOneField(File, on_delete=models.CASCADE, db_column='FileID')
    actividad_verificacion = models.ForeignKey(ActividadVerificacion, on_delete=models.CASCADE, db_column='ActividadVerificacionID')  # Nueva relación
    file_status = models.CharField(max_length=255, db_column='Status') 
    verified_count = models.IntegerField(default=0, db_column='Count') 
    total_verifications = models.IntegerField(default=0, db_column='VerificationsTotal')  

    class Meta:
        db_table = 'VerificationFile'
