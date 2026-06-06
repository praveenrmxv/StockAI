from django.urls import path
from . import views
from django.contrib.auth import views as auth_views


urlpatterns = [
    path('', views.home),
    path('inventory/', views.inventory),
    path('login/', views.login_view, name='login'),
    path('dashboard/', views.dashboard),
    path('upload/', views.upload_csv),
    path('profile/', views.profile),
    path('logout/', auth_views.LogoutView.as_view(next_page='/login/')),
    # path('logout/', auth_views.LogoutView.as_view(next_page='/login/'), name='logout'),
]