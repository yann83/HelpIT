# EXEMPLE AVEC SHELL=TRUE - À UTILISER AVEC PRUDENCE POUR LE DIAGNOSTIC
import subprocess

# self.current_ip = "192.168.1.100" # Exemple

try:
    # Notez que si shell=True, la commande est passée en une seule chaîne.
    # Vous devrez peut-être ajuster les guillemets si self.current_ip contient des espaces ou des caractères spéciaux.
    command_string = f'msra.exe /offerra s118301-121-900'
    result = subprocess.run(command_string, shell=True, check=True, capture_output=True, text=True)
    print("Commande exécutée avec succès (avec shell=True).")
    print("Stdout:", result.stdout)
    print("Stderr:", result.stderr)
except subprocess.CalledProcessError as e:
    print(f"Erreur lors de l'exécution de la commande (avec shell=True) : {e}")
    print("Stdout:", e.stdout)
    print("Stderr:", e.stderr)
except FileNotFoundError:
    print(f"Erreur : Commande '{command_string}' n'a pas été trouvée par le shell.")