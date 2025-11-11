from django.urls import path
from .views import GenerateTokenView, StartCallView, EndCallView


urlpatterns = [
    path('token/', GenerateTokenView.as_view(), name='agora-generate-token'),
    path('start/', StartCallView.as_view(), name='agora-start-call'),
    path('end/', EndCallView.as_view(), name='agora-end-call'),
]