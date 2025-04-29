from django.db import models
from Authentication.models  import Users

# Create your models here.
class Comment(models.Model):
    usuario = models.ForeignKey(Users, on_delete=models.CASCADE, db_column='UserID')
    descripcion = models.TextField(db_column='Description')
    created = models.DateTimeField(auto_now_add=True, db_column='CreatedDate')

    class Meta:
        db_table = 'Comment'