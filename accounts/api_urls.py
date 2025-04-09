from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .api_views import CustomTokenObtainPairView, UserProfileUpdateView

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileUpdateView.as_view(), name='user-profile-update'),
] 