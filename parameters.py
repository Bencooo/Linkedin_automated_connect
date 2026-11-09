"""Paramètres. Les identifiants viennent du fichier .env (voir .env.example)."""
import os

from dotenv import load_dotenv

load_dotenv()

linkedin_username = os.getenv("LINKEDIN_USERNAME", "")
linkedin_password = os.getenv("LINKEDIN_PASSWORD", "")

profiles_file = "profiles.csv"        # colonnes url;note (note vide = sans note)
results_file = "invitations.csv"      # journal : url;nom;statut;note;date
max_invites_per_run = 20              # limite par lancement (rester prudent)
min_delay_seconds = 30                # pause aléatoire entre deux profils
max_delay_seconds = 90
