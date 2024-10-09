# Bonjour ! Ce projet concerne l'application G+ pour [MADA-Digital](https://mada-digital.net)

## Description
Projet G+ est une application web développée avec le framework Django et stylisée avec TailwindCSS. Ce projet vise à fournir une interface utilisateur moderne et réactive.

## Prérequis
- Python 3.9+
- Django 3.2.6+
- Node.js et npm

## Installation

### Cloner le dépôt
```bash
git clone https://github.com/votre-utilisateur/projet-g-plus.git
cd projet-g-plus
```

### Créer et activer un environnement virtuel
```bash
python -m venv env
source env/bin/activate  # Sur Windows, utilisez `env\Scripts\activate`
```

### Installer les dépendances Python
```bash
pip install -r requirements.txt
```

### Installer TailwindCSS
```bash
python manage.py tailwind install
```
## Lancer le serveur de développement
```bash
python manage.py runserver
python manage.py tailwind start
```

## Utilisation
Ouvrez votre navigateur et accédez à http://127.0.0.1:8000 pour voir votre application en action 🎉.

## Pour ajouter un autre module, utilisez la commande suivante :  
```bash
python manage.py startapp nom_projet
```

Consultez la documentation de Django pour plus de détails.

## Licence
Ce projet est sous licence MIT. Voir le fichier LICENSE pour plus de détails. Tout droit réserver par [MADA-Digital](https://mada-digital.net)
 😊