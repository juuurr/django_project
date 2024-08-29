from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    # blog 앱 내부의 경로를 지정할 부분
    # path('login/', views.user_login) #localhost:8000/account/login 경로 호출

    #장고의 view 사용 teplates/registration/
    path('login/', auth_views.LoginView.as_view()), 
    path('logout/', auth_views.LogoutView.as_view()) #주소로 접근해서 콘솔에 405가 뜸을 확인함
]
