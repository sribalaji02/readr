from django.urls import path
from . import views

urlpatterns = [
    path('signup/', views.signup, name="signup"),
    path('login/', views.login, name = "login"),
    path('logout/', views.logout, name = "logout"),
    path('validate/', views.validate, name = "validate"),
    path('forgot/',views.forgot,name="forgot"),
    path('forgot_val/',views.forgot_val,name="forgot_val"),
    path('home/<name>', views.home, name = "home"),
    path('downloads/<name>', views.downloads, name = "downloads"),
    path('readr/<name>', views.readr, name = "readr"),
    path('indexer/<name>', views.indexer, name = "indexer"),
    path('chapterchat/<name>', views.chapterchat, name='chapterchat'),

]
