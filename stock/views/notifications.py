from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, View
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from ..models import Notification


class NotificationListView(LoginRequiredMixin, ListView):
    """Vue pour afficher la liste des notifications de l'utilisateur."""
    model = Notification
    template_name = 'stock/notifications/liste.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        return Notification.objects.filter(
            utilisateur=self.request.user
        ).order_by('-date_creation')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = _("Mes notifications")
        # Marquer les notifications comme vues lors de l'affichage
        Notification.objects.filter(
            utilisateur=self.request.user,
            vue=False
        ).update(vue=True)
        return context


class NotificationMarkAsReadView(LoginRequiredMixin, View):
    """Vue pour marquer une notification comme lue."""
    
    def post(self, request, *args, **kwargs):
        notification = get_object_or_404(
            Notification,
            id=kwargs.get('pk'),
            utilisateur=request.user
        )
        notification.marquer_comme_vue()
        return JsonResponse({'status': 'success'})


class NotificationMarkAllAsReadView(LoginRequiredMixin, View):
    """Vue pour marquer toutes les notifications comme lues."""
    
    def post(self, request, *args, **kwargs):
        updated = Notification.objects.filter(
            utilisateur=request.user,
            vue=False
        ).update(vue=True)
        
        return JsonResponse({
            'status': 'success',
            'count_updated': updated
        })


class NotificationCountView(LoginRequiredMixin, View):
    """Vue pour récupérer le nombre de notifications non lues."""
    
    def get(self, request, *args, **kwargs):
        count = Notification.objects.filter(
            utilisateur=request.user,
            vue=False
        ).count()
        
        return JsonResponse({
            'status': 'success',
            'count': count
        })
