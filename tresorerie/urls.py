from django.urls import path
from .views import ( KPIView, ScheduleView, TraiteView, PeriodView )

urlpatterns = [
    path("kpis/", KPIView.as_view()),
    path("schedule/", ScheduleView.as_view(), name="schedule"),
    path("traites/", TraiteView.as_view(), name="traites"),
    path('period/', PeriodView.as_view()),
]