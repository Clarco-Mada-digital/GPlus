/**
 * Gestion de Stock - Main JavaScript
 * Contient les fonctions utilitaires et les gestionnaires d'événements
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialisation des composants
    initMobileMenu();
    initDataTables();
    initSelect2();
    initDatePickers();
    initTooltips();
    initModals();
    initFormValidation();
    
    // Gestion des messages flash
    autoDismissAlerts();
    
    // Autres initialisations
    initProductSearch();
    initStockCalculations();
    initNotifications();

    // Vérifier périodiquement les nouvelles notifications (toutes les 5 minutes)
    if (document.getElementById('notification-counter')) {
        setInterval(checkNewNotifications, 5 * 60 * 1000);
    }
});

/**
 * Initialise le menu mobile
 */
function initMobileMenu() {
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
        
        // Fermer le menu lors du clic en dehors
        document.addEventListener('click', function(event) {
            if (!mobileMenuButton.contains(event.target) && !mobileMenu.contains(event.target)) {
                mobileMenu.classList.add('hidden');
            }
        });
    }
}

/**
 * Initialise les DataTables pour les tableaux
 */
function initDataTables() {
    const tables = document.querySelectorAll('table.datatable');
    
    if (tables.length > 0 && typeof $.fn.DataTable === 'function') {
        tables.forEach(table => {
            $(table).DataTable({
                responsive: true,
                language: {
                    url: '//cdn.datatables.net/plug-ins/1.10.25/i18n/French.json'
                },
                dom: "<'flex flex-col md:flex-row justify-between mb-4'<'mb-4 md:mb-0'l><'flex items-center'f>>" +
                      "<'w-full overflow-x-auto'tr>" +
                      "<'flex flex-col md:flex-row justify-between items-center mt-4'<'mb-4 md:mb-0'i><'pagination flex space-x-2'>p>"
            });
        });
    }
}

/**
 * Initialise les sélecteurs Select2
 */
function initSelect2() {
    if (typeof $.fn.select2 === 'function') {
        $('select.select2').select2({
            theme: 'tailwind',
            width: '100%',
            placeholder: 'Sélectionnez une option',
            allowClear: true
        });
    }
}

/**
 * Initialise les sélecteurs de date
 */
function initDatePickers() {
    if (typeof flatpickr !== 'undefined') {
        flatpickr('.datepicker', {
            dateFormat: 'Y-m-d',
            locale: 'fr',
            allowInput: true
        });
    }
}

/**
 * Initialise les tooltips
 */
function initTooltips() {
    if (typeof tippy === 'function') {
        tippy('[data-tippy-content]', {
            animation: 'scale',
            theme: 'light',
            arrow: true
        });
    }
}

/**
 * Initialise les modales
 */
function initModals() {
    // Fermer les modales lors du clic sur le bouton de fermeture
    document.querySelectorAll('.modal-close').forEach(button => {
        button.addEventListener('click', function() {
            const modal = this.closest('.modal');
            if (modal) {
                modal.classList.add('hidden');
            }
        });
    });
    
    // Fermer la modale en cliquant en dehors
    document.querySelectorAll('.modal').forEach(modal => {
        modal.addEventListener('click', function(e) {
            if (e.target === this) {
                this.classList.add('hidden');
            }
        });
    });
    
    // Boutons pour ouvrir les modales
    document.querySelectorAll('[data-modal]').forEach(button => {
        button.addEventListener('click', function() {
            const modalId = this.getAttribute('data-modal');
            const modal = document.getElementById(modalId);
            if (modal) {
                modal.classList.remove('hidden');
                
                // Mettre le focus sur le premier élément focusable
                const focusable = modal.querySelector('input, button, [tabindex]');
                if (focusable) {
                    focusable.focus();
                }
            }
        });
    });
}

/**
 * Initialise la validation des formulaires
 */
function initFormValidation() {
    // Exemple de validation personnalisée
    const forms = document.querySelectorAll('form[novalidate]');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            
            form.classList.add('was-validated');
        }, false);
    });
}

/**
 * Ferme automatiquement les alertes après un délai
 */
function autoDismissAlerts() {
    const alerts = document.querySelectorAll('.alert[data-auto-dismiss]');
    
    alerts.forEach(alert => {
        const delay = parseInt(alert.getAttribute('data-auto-dismiss') || '5000', 10);
        
        setTimeout(() => {
            alert.style.transition = 'opacity 0.5s';
            alert.style.opacity = '0';
            
            setTimeout(() => {
                alert.remove();
            }, 500);
        }, delay);
    });
}

/**
 * Initialise la recherche de produits
 */
function initProductSearch() {
    const searchInput = document.getElementById('product-search');
    
    if (searchInput) {
        // Utilisation de debounce pour limiter les appels
        let debounceTimer;
        
        searchInput.addEventListener('input', function() {
            clearTimeout(debounceTimer);
            
            debounceTimer = setTimeout(() => {
                const query = this.value.trim();
                
                if (query.length >= 2) {
                    // Implémenter la recherche AJAX ici
                    console.log('Recherche de produits:', query);
                }
            }, 300);
        });
    }
}

/**
 * Initialise les calculs de stock
 */
function initStockCalculations() {
    // Calcul automatique du total pour les entrées/sorties
    const quantityInputs = document.querySelectorAll('input[name*="quantite"]');
    const priceInputs = document.querySelectorAll('input[name*="prix_unitaire"]');
    const totalElements = document.querySelectorAll('[data-total]');
    
    function calculateTotal() {
        let quantity = parseFloat(quantityInputs[0]?.value) || 0;
        let price = parseFloat(priceInputs[0]?.value) || 0;
        let total = quantity * price;
        
        totalElements.forEach(element => {
            element.textContent = total.toFixed(2) + ' FCFA';
        });
    }
    
    quantityInputs.forEach(input => {
        input.addEventListener('input', calculateTotal);
    });
    
    priceInputs.forEach(input => {
        input.addEventListener('input', calculateTotal);
    });
}

/**
 * Affiche une notification toast
 * @param {string} message - Le message à afficher
 * @param {string} type - Le type de notification (success, error, warning, info)
 * @param {number} duration - Durée d'affichage en ms (par défaut: 5000ms)
 */
function showToast(message, type = 'info', duration = 5000) {
    const toastContainer = document.getElementById('toast-container');
    
    if (!toastContainer) return;
    
    const toast = document.createElement('div');
    toast.className = `toast ${type} fixed bottom-4 right-4 p-4 rounded shadow-lg text-white mb-2 transition-all duration-300 transform translate-x-0 opacity-100`;
    toast.textContent = message;
    
    toastContainer.appendChild(toast);
    
    // Animation d'entrée
    setTimeout(() => {
        toast.style.transform = 'translateX(0)';
    }, 10);
    
    // Suppression après la durée spécifiée
    setTimeout(() => {
        toast.style.transform = 'translateX(100%)';
        toast.style.opacity = '0';
        
        setTimeout(() => {
            toast.remove();
        }, 300);
    }, duration);
}

/**
 * Confirme une action avant soumission
 * @param {Event} event - L'événement de soumission
 * @param {string} message - Le message de confirmation
 * @returns {boolean}
 */
function confirmAction(event, message = 'Êtes-vous sûr de vouloir effectuer cette action ?') {
    if (!confirm(message)) {
        event.preventDefault();
        return false;
    }
    return true;
}

/**
 * Initialise la gestion des notifications
 */
function initNotifications() {
    // Marquer une notification comme lue au clic
    document.querySelectorAll('.mark-as-read').forEach(button => {
        button.addEventListener('click', function(e) {
            e.preventDefault();
            const notificationId = this.dataset.notificationId;
            markNotificationAsRead(notificationId, this.closest('[data-notification-id]'));
        });
    });

    // Marquer toutes les notifications comme lues
    const markAllReadBtn = document.getElementById('mark-all-read');
    if (markAllReadBtn) {
        markAllReadBtn.addEventListener('click', function(e) {
            e.preventDefault();
            markAllNotificationsAsRead();
        });
    }
}

/**
 * Marque une notification comme lue
 * @param {string} notificationId - L'ID de la notification
 * @param {HTMLElement} element - L'élément DOM de la notification
 */
function markNotificationAsRead(notificationId, element) {
    if (!notificationId) return;
    
    fetch(`/notifications/${notificationId}/marquer-lue/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Mettre à jour l'interface utilisateur
            if (element) {
                element.classList.remove('bg-blue-50');
                const badge = element.querySelector('.mark-as-read');
                if (badge) badge.remove();
            }
            updateNotificationCounter(-1);
        }
    })
    .catch(error => console.error('Erreur lors du marquage de la notification comme lue:', error));
}

/**
 * Marque toutes les notifications comme lues
 */
function markAllNotificationsAsRead() {
    fetch('/notifications/marquer-toutes-lues/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken'),
            'Content-Type': 'application/json',
        },
        credentials: 'same-origin',
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            // Mettre à jour l'interface utilisateur
            document.querySelectorAll('.mark-as-read').forEach(btn => btn.remove());
            document.querySelectorAll('[data-notification-id]').forEach(el => {
                el.classList.remove('bg-blue-50');
            });
            updateNotificationCounter(0);
        }
    })
    .catch(error => console.error('Erreur lors du marquage de toutes les notifications comme lues:', error));
}

/**
 * Vérifie les nouvelles notifications
 */
function checkNewNotifications() {
    fetch('/api/notifications/count/')
        .then(response => response.json())
        .then(data => {
            if (data.unread_count !== undefined) {
                updateNotificationCounter(data.unread_count);
            }
        })
        .catch(error => console.error('Erreur lors de la vérification des nouvelles notifications:', error));
}

/**
 * Met à jour le compteur de notifications
 * @param {number} count - Le nouveau nombre de notifications non lues (ou delta si delta=true)
 * @param {boolean} delta - Si true, le count est ajouté au compteur actuel
 */
function updateNotificationCounter(count, delta = false) {
    const counter = document.getElementById('notification-counter');
    if (!counter) return;

    let newCount = delta ? (parseInt(counter.textContent) + count) : count;
    
    // S'assurer que le compteur ne soit pas négatif
    newCount = Math.max(0, newCount);
    
    // Mettre à jour le compteur
    counter.textContent = newCount;
    
    // Afficher ou masquer le compteur
    if (newCount > 0) {
        counter.classList.remove('hidden');
    } else {
        counter.classList.add('hidden');
    }
    
    // Jouer une animation pour attirer l'attention sur les nouvelles notifications
    if (count > 0) {
        const bell = document.querySelector('.fa-bell');
        if (bell) {
            bell.classList.add('animate-bell');
            setTimeout(() => bell.classList.remove('animate-bell'), 1000);
        }
    }
}

/**
 * Récupère la valeur d'un cookie par son nom
 * @param {string} name - Le nom du cookie
 * @returns {string|null} La valeur du cookie ou null si non trouvé
 */
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

// Exposer les fonctions globales
window.GStock = {
    showToast,
    confirmAction,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    updateNotificationCounter
};
