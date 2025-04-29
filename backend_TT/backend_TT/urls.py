from django.contrib import admin
from django.urls import include, path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib import admin
from django.urls import path
from Authentication import views as endpointAuthentication 
from Beca import views as endpointBeca
from Files import views as endpointFiles
from Tasks import views as endpointTasks
from Comments import views as endpointComments

urlpatterns = [
    path('admin/', admin.site.urls),

    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

    path('api/authentication/signin/', endpointAuthentication.register, name='register'),
    path('api/authentication/login/', endpointAuthentication.login, name='login'),
    path('api/authentication/recover_password_login/', endpointAuthentication.reset_password, name='reset_password'),
    path('api/authentication/recover_password/', endpointAuthentication.recover_password, name='recover_password'),
    path('api/authentication/profile_user/', endpointAuthentication.get_user_info, name='profile'),

    path('api/beca/list_beca/', endpointBeca.list_becas, name='list_beca'),
    path('api/beca/list_beca/edd', endpointBeca.get_activities_edd, name='list_activities_edd'),
    path('api/beca/list_beca/edi', endpointBeca.get_activities_edi, name='list_activities_edi'),

    path('api/user/activities/', endpointTasks.get_user_tasks, name='get_user_activities'),
    path('api/user/activities/full', endpointTasks.get_all_user_tasks, name='get_all_user_activities'),
    path('api/user/activities/create', endpointTasks.create_task, name='create_activities'),
    path('api/user/tasks/<int:task_id>/delete', endpointTasks.delete_task_with_files, name='delete_activities'),
    path('api/user/activities/<int:task_id>/details', endpointTasks.get_task_details, name='details_for_activitie'),
    path('api/user/activities/<int:task_id>/update', endpointTasks.update_task, name='update_activities'),
    path('api/user/tasks/edd', endpointTasks.get_tasks_edd, name='get_tasks_edd'),
    path('api/user/tasks/edi', endpointTasks.get_tasks_edi, name='get_tasks_edi'),

    path('api/upload_pdf/<int:task_id>/', endpointFiles.upload_pdf, name='upload_pdf'),
    path('api/files/<int:task_id>/', endpointFiles.get_files_for_task, name='get_files_for_task'),
    path('api/filesEstado/<int:task_id>/', endpointFiles.get_files_with_status, name='get_files_with_status'),
    path('api/files/activities/all/', endpointFiles.get_all_user_activities_files, name='get_all_user_activities_files'),
    path('api/view_pdf/<file_id>/', endpointFiles.view_pdf, name='view_pdf'),
    path('api/files/delete/<file_id>/', endpointFiles.delete_file, name='delete_file'),
    path('api/files/verificacion/', endpointFiles.get_files_with_actividad_verificacion, name='get_files_with_actividad_verificacion'),
    path('api/files/verificacion/<file_id>/', endpointFiles.get_verificaciones_by_file, name='get_verificaciones_by_file'),
    path('api/files/verificacion/<file_id>/update', endpointFiles.update_verificaciones_by_file, name='update_verificaciones_by_file'),
    path('api/files/verificacion/<file_id>/info', endpointFiles.get_verification_status_and_count, name='get_verification_status_and_count'),

    path('api/comments/create', endpointComments.create_comment, name='create_comment'),
    path('api/comments/obtener', endpointComments.get_all_comments, name='get_all_comments'),
]
