"""Paramètres. Les identifiants viennent du fichier .env (voir .env.example)."""
import os

from dotenv import load_dotenv

load_dotenv()

linkedin_username = os.getenv("LINKEDIN_USERNAME", "")
linkedin_password = os.getenv("LINKEDIN_PASSWORD", "")

# Recherche / envoi d'invitations (désactivé pour l'instant)
file_name = "connections.csv"
keywords = "Freelance,consultant,fullstack"
ignore_list = "Person1,Person2"
till_page = 100

# --- Mode "liste de liens" (connect_profiles.py) ---
profiles_file = "profiles.txt"        # un lien de profil par ligne
results_file = "invitations.csv"      # journal : url;statut;date
max_invites_per_run = 20              # limite par lancement (rester prudent)
min_delay_seconds = 30                # pause aléatoire entre deux profils
max_delay_seconds = 90

# Note jointe à l'invitation ("" = pas de note). {prenom} = prénom du profil. Max 300 caractères.
# Si la note est impossible (quota gratuit atteint…), le script envoie sans note.
connection_note = "Bonjour {prenom}, je serais ravi de vous compter dans mon réseau."
