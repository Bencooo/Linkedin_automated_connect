# LinkedIn – envoi d'invitations depuis une liste de profils

Se connecte à LinkedIn (session Chrome conservée) puis envoie une invitation à chaque
profil d'un fichier CSV, avec une note personnalisée si elle est fournie.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install selenium webdriver-manager python-dotenv
```

## Configuration

1. Copiez `.env.example` en `.env` et renseignez `LINKEDIN_USERNAME` et `LINKEDIN_PASSWORD`
   (ce fichier est ignoré par git, ne le committez jamais).
2. Créez `profiles.csv` (modèle : `profiles.example.csv`), séparateur `;` :

   ```csv
   url;note
   https://www.linkedin.com/in/exemple-1/;Bonjour Marie, ravi d'échanger avec vous.
   https://www.linkedin.com/in/exemple-2/;
   ```

   Une note vide = invitation sans note. La note est limitée à 300 caractères ; si elle est
   impossible (quota LinkedIn atteint…), l'invitation part sans note.
3. Réglages optionnels dans `parameters.py` : limite d'invitations par lancement, pauses entre profils.

## Utilisation

```bash
python connect_profiles.py
```

- Première fois : connexion automatique (un code ou un captcha éventuel se fait à la main).
  Ensuite la session est réutilisée (`.chrome_profile/`).
- Le journal `invitations.csv` contient une ligne par profil : `url;nom;statut;note;date`.
  Statuts : `ENVOYE`, `EN_ATTENTE`, `INDISPONIBLE`, `ERREUR`. Les profils `ENVOYE` / `EN_ATTENTE`
  sont ignorés aux lancements suivants ; les autres sont retentés (la ligne est mise à jour).
- En cas d'`ERREUR` ou d'`INDISPONIBLE`, une capture et le HTML de la page sont sauvegardés dans `debug/`.

## Fichiers

| Fichier | Rôle |
|---|---|
| `connect_profiles.py` | script principal |
| `linkedin_session.py` | lancement de Chrome et connexion |
| `parameters.py` | identifiants (via `.env`) et réglages |
| `profiles.csv` / `invitations.csv` / `.env` / `.chrome_profile/` / `debug/` | locaux, ignorés par git |

L'ancien bot (recherche par mots-clés et envoi en masse) est conservé sur la branche `legacy-search-bot`.
