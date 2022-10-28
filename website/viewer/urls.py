from django.urls import path
from . import views

urlpatterns = [
    path("dashboard/", views.dashboard, name="dashboard"),
    path("commited/", views.commited, name="commited"),
    path("staging/", views.staging, name="staging"),
    path("queue/", views.queue, name="queue"),
    path("revision/<str:hash>/", views.revision, name="revision"),
    path("job/<int:pk>/", views.job, name="job"),
    path("job/compare/<int:pk1>/<int:pk2>/", views.job_compare, name="job_compare"),
    path("cts_result/<int:pk>/", views.cts_result, name="cts_result"),
    path("", views.index, name="index"),
]
