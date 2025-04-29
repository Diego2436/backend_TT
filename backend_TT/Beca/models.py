from django.db import models

class Beca(models.Model):
    nombre = models.CharField(max_length=255, db_column='Name')
    descripcion = models.CharField(max_length=255, blank=True, db_column='Description')

    class Meta:
        db_table = 'Beca'

class ActividadBeca(models.Model):
    codigo = models.CharField(max_length=30, db_column='Code')
    nombre = models.TextField(db_column='Name')
    beca = models.ForeignKey(Beca, on_delete=models.CASCADE, db_column='BecaID')

    class Meta:
        db_table = 'ActivitiesBeca'

class Verificacion(models.Model):
    name = models.CharField(max_length=255, db_column='Name') 
    description = models.CharField(max_length=255, db_column='Description')

    class Meta:
        db_table = 'Verification' 

class ActividadVerificacion(models.Model):
    actividadBeca = models.ForeignKey(ActividadBeca, related_name='verificaciones', on_delete=models.CASCADE, db_column='ActivityID')  
    verificacion = models.ForeignKey(Verificacion, related_name='actividades', on_delete=models.CASCADE, db_column='VerificationID')

    class Meta:
        db_table = 'ActivityVerification'