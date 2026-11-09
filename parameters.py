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
