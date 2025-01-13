[33mcommit 12bef4c67514b8396bcfdaf78eeb47ce02a9d615[m[33m ([m[1;36mHEAD[m[33m -> [m[1;32mmain[m[33m, [m[1;31morigin/main[m[33m, [m[1;31morigin/HEAD[m[33m)[m
Author: clark <clarco.dev@mada-digital.net>
Date:   Thu Jan 9 14:34:54 2025 +0300

    Mise a jour du fichier settings

[1mdiff --git a/GPP/settings.py b/GPP/settings.py[m
[1mindex 8f1a929..9563c16 100644[m
[1m--- a/GPP/settings.py[m
[1m+++ b/GPP/settings.py[m
[36m@@ -86,11 +86,22 @@[m [mWSGI_APPLICATION = 'GPP.wsgi.application'[m
 # Database[m
 # https://docs.djangoproject.com/en/5.1/ref/settings/#databases[m
 [m
[31m-DATABASES = {[m
[32m+[m[32mDATABASES = {[m[41m    [m
     'default': {[m
[32m+[m[32m        'ENGINE': 'django.db.backends.mysql',[m
[32m+[m[32m        'NAME': 'gplus',[m
[32m+[m[32m        'USER': 'root',[m
[32m+[m[32m        'PASSWORD': '',[m
[32m+[m[32m        'HOST':'127.0.0.1',[m
[32m+[m[32m        'PORT': '3306',[m
[32m+[m[32m        'OPTIONS': {[m
[32m+[m[32m            'sql_mode': 'STRICT_TRANS_TABLES,NO_ENGINE_SUBSTITUTION',[m
[32m+[m[32m        }[m
[32m+[m[32m    },[m
[32m+[m[32m    'local': {[m
         'ENGINE': 'django.db.backends.sqlite3',[m
         'NAME': BASE_DIR / 'db.sqlite3',[m
[31m-    }[m
[32m+[m[32m    },[m
 }[m
 [m
 [m
