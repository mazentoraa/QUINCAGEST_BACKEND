from django.urls import path
from .views import ( KPIView, ScheduleView, TraiteView, PeriodView )

urlpatterns = [
    path("api/kpis/", KPIView.as_view()),
    path("api/schedule/", ScheduleView.as_view(), name="schedule"),
    path("api/traites/", TraiteView.as_view(), name="traites"),
    path('api/period/', PeriodView.as_view()),
]