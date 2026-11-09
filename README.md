![](https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Logo.svg.original.svg)
# LinkedIn Networking

Code Python pour étendre automatiquement votre réseau LinkedIn en fonction de vos intérêts.





## Prérequis

Utilisez le gestionnaire de paquets [pip](https://pip.pypa.io/en/stable/) pour installer selenium.

```bash
pip install selenium
pip install webdriver-manager
pip install python-dotenv
```

## Comment utiliser ?
 - Copiez `.env.example` en `.env` et renseignez `LINKEDIN_USERNAME` et `LINKEDIN_PASSWORD` (ce fichier est ignoré par git, ne le committez jamais).
 - Les autres paramètres (mots clés, pages, etc.) se trouvent dans `parameters.py`.
 - Exécutez `python linkedIn.py`

Pour l'instant, seule la connexion est active ; la recherche et l'envoi d'invitations sont désactivés.
