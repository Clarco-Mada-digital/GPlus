from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.routers import DefaultRouter
from .views import (DashboardAPIView, CustomPasswordChangeView, CustomPasswordChangeDoneView,
                    ManageEmployeePermissionsView, ApprouverCongeView, MarkNotificationAsReadView,
                    NotificationListView, HistoriqueListView, ProfileAPIView,
                    EmployeeViewSet, CongeViewSet, ScheduleViewSet, AgendaEventViewSet,
                    PaieViewSet, ExportFicheDePaiePDFView, SettingsView, ExportDatabaseView, profile_view,
                    )

router = DefaultRouter()
router.register(r'employees', EmployeeViewSet)
router.register(r'conges', CongeViewSet, basename='conge')
conge_list = CongeViewSet.as_view({'get': 'get_conges_for_employee'})
router.register(r'schedules', ScheduleViewSet)
router.register(r'agenda-events', AgendaEventViewSet)
router.register(r'payrolls', PaieViewSet, basename='payroll')


urlpatterns = [

                  path('api/', include(router.urls)),  # Ajoute 'api/' devant toutes les URL des routeurs

                  path('api/dashboard/', DashboardAPIView.as_view(), name='dashboard'),

                  path('employee/create/', EmployeeViewSet.as_view({'get': 'create_employee_form', 'post': 'create_employee_form'}),
                         name='employee-creates'),

                   path('api/notifications/', NotificationListView.as_view(), name='notifications_list'),
                  path('api/notifications/<int:notification_id>/mark-as-read/', MarkNotificationAsReadView.as_view(),
                       name='mark_notification_as_read'),

                  path('api/historique/historique_list', HistoriqueListView.as_view(), name='historique_list'),

                  path('api/settings/', SettingsView.as_view(), name='settings'),
                  path('api/password_change/', CustomPasswordChangeView.as_view(), name='password_change'),
                  path('api/password_change/done/', CustomPasswordChangeDoneView.as_view(), name='password_change_done'),
                  path('export-db/', ExportDatabaseView.as_view(), name='export_database'),

                  path('api/employees/<int:employee_id>/conges/', conge_list, name='conge_for_employee'),
                  path('api/conge/<int:conge_id>/<str:action>/', ApprouverCongeView.as_view(), name='approuver_conge'),

                  path('api/manage_permissions/', ManageEmployeePermissionsView.as_view(),name='manage_employee_permissions'
                       ),
                     path('profile/', profile_view, name='profile'),

                    path('api/accounts/profile/', ProfileAPIView.as_view(), name='profile-api'),

                  path('api/payrolls/export_pdf/<int:id>/', ExportFicheDePaiePDFView.as_view(),
                       name='export_fiche_de_paie_pdf'),

              ]
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
