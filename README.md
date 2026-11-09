> ## ⚠️ Utilisez la branche `connect-from-links`
> Cette branche (`main`) contient l'**ancien bot** (recherche par mots-clés), qui n'est plus maintenu
> et dont le login ne fonctionne plus. **La version fonctionnelle est sur la branche
> [`connect-from-links`](../../tree/connect-from-links)** : envoi d'invitations à partir d'un CSV de
> liens de profils (`url;note`). Son README explique tout : installation, format du CSV, lancement.
>
> ```bash
> git checkout connect-from-links
> ```

![](https://content.linkedin.com/content/dam/me/business/en-us/amp/brand-site/v2/bg/LI-Logo.svg.original.svg)
# LinkedIn Networking

Code Python pour étendre automatiquement votre réseau LinkedIn en fonction de vos intérêts.





## Prérequis

Utilisez le gestionnaire de paquets [pip](https://pip.pypa.io/en/stable/) pour installer selenium.

```bash
pip install selenium
pip install webdriver-manager
```

## Comment utiliser ?
 - Ouvrez le fichier parameters.py et indiquez votre adresse email, votre mot de passe et des mots clés pour les critères de recherche.
 - Exécutez `python linkedIn.py`
