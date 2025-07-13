from django.urls import path, include
from . import views
from .views import direct_chat, mark_day, get_daily_status, get_diary, update_plan, conversation_detail
from .diary_api import direct_chat_with_diary

urlpatterns = [
    path('ask/', views.chatbot_api),
    path('recommend/', views.recommend_literature),
    path('generate_plan/', views.generate_plan),
    path('my_plans/', views.my_plans),
    path('join_plan/', views.join_plan),
    path('agent_chat/', views.agent_chat),
    path('direct_chat/', direct_chat),
    path('mark_day/', mark_day),
    path('get_daily_status/', get_daily_status),
    path('get_diary/', get_diary),
    path('direct_chat_with_diary/', direct_chat_with_diary),
    path('update_plan/', update_plan),
    path('messages/', views.message_list),
    path('conversations/', views.conversation_list),
    path('conversations/<int:id>/', conversation_detail),
    path('emotion_curve/', views.emotion_curve),
]