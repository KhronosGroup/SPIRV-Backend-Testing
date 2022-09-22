from django.urls import path

from . import views

urlpatterns = [
    path("job/<int:pk>/", views.JobDetail.as_view()),
    path("dispatch/", views.Dispatch.as_view()),
    path("job/<int:job_pk>/lit/", views.LitResultDetail.as_view()),
    path("job/<int:job_pk>/cts/", views.CtsResultDetail.as_view()),
]
