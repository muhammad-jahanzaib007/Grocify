from django.urls import path
from . import views

app_name = 'reports'

urlpatterns = [
    path('', views.reports_dashboard, name='index'),
    path('snapshots/', views.DamageReportSnapshotListView.as_view(), name='snapshot_list'),
    path('snapshots/create/', views.DamageReportSnapshotCreateView.as_view(), name='snapshot_create'),
    path('snapshots/<int:pk>/', views.DamageReportSnapshotDetailView.as_view(), name='snapshot_detail'),
    path('snapshots/<int:pk>/update/', views.DamageReportSnapshotUpdateView.as_view(), name='snapshot_update'),
    path('snapshots/<int:pk>/delete/', views.DamageReportSnapshotDeleteView.as_view(), name='snapshot_delete'),
]