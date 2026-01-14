from credential import Application

# Initialiser
app = Application()

# Authentification (gère automatiquement création ou connexion)
if not app.demarrer():
    exit()

# Utiliser les credentials quand nécessaire
credentials = app.executer_fonction_admin("Ma_Fonction")
password_admin = credentials['password']

# À la fermeture
app.fermer()
