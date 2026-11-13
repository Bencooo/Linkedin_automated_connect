# LinkedIn – envoi d'invitations depuis une liste de profils

> **Version à utiliser : la branche `connect-from-links`** (celle-ci). C'est la seule
> version fonctionnelle et testée (novembre 2026). Les autres branches sont conservées pour mémoire.

## Les versions du projet

| Branche | Ce que c'est | Statut |
|---|---|---|
| **`connect-from-links`** | **Envoie des invitations à une liste de liens de profils fournie dans un CSV** (avec une note personnalisée par profil, optionnelle). | ✅ **Fonctionnelle, à utiliser** |
| `legacy-search-bot` (= `main`) | Ancien bot : tape des mots-clés dans la recherche LinkedIn, parcourt les pages de résultats et clique « Se connecter » sur tout le monde. Identifiants en clair dans `parameters.py`. | ⚠️ Conservé tel quel, non maintenu : son login ne fonctionne plus avec le LinkedIn actuel |
| `agent-integration` | `connect-from-links` + options de ligne de commande, arrêt propre et attente du chargement du profil. **À utiliser avec LinkedIn Agent** (bouton « Lancer le bot »). | ✅ Fonctionnelle |
| `cleanup-login-env` | Étape intermédiaire : login réparé, identifiants dans `.env`, session Chrome persistante, sans envoi d'invitations. | Historique |

Pour utiliser la bonne version : `git checkout connect-from-links`.

## Comment ça marche (`connect-from-links`)

1. Vous fournissez un fichier `profiles.csv` : un profil par ligne, avec sa note éventuelle.
2. Le script ouvre Chrome (profil dédié, la session est conservée) et se connecte à LinkedIn si besoin.
3. Pour chaque profil : il ouvre la page, clique « Se connecter » (directement ou via le menu « … »),
   ajoute la note si elle existe, puis envoie. Si la note est impossible (quota LinkedIn atteint…),
   l'invitation part **sans note**.
4. Il vérifie que le bouton appartient bien au profil visité (jamais une suggestion « Autres profils »).
5. Il fait une pause aléatoire entre deux profils, s'arrête à la limite par lancement
   (20 par défaut) et note chaque résultat dans `invitations.csv`.

## Installation

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install selenium webdriver-manager python-dotenv
```

Chrome doit être installé.

## Configuration

**1. Identifiants** : copiez `.env.example` en `.env` et renseignez
`LINKEDIN_USERNAME` et `LINKEDIN_PASSWORD` (fichier ignoré par git, ne le committez jamais).

**2. Le CSV des profils** : créez `profiles.csv` (modèle : `profiles.example.csv`).
Séparateur `;`, en-tête obligatoire, deux colonnes :

| Colonne | Contenu |
|---|---|
| `url` | lien du profil LinkedIn (obligatoire) |
| `note` | texte de la note jointe à l'invitation, 300 caractères max. **Vide = sans note.** |

```csv
url;note
https://www.linkedin.com/in/exemple-1/;Bonjour Marie, ravi d'échanger avec vous sur vos recherches de profils.
https://www.linkedin.com/in/exemple-2/;
```

Si une note contient un `;`, mettez-la entre guillemets. Pas de retour à la ligne dans une note.

**3. Réglages** (optionnel, `parameters.py`) : `max_invites_per_run` (20), `min_delay_seconds` /
`max_delay_seconds` (pause de 30 à 90 s entre deux profils). Restez prudent : LinkedIn limite les
invitations et peut restreindre un compte qui en envoie trop vite.

## Lancer

```bash
python connect_profiles.py
```

Première fois : connexion automatique (un code ou un captcha éventuel se fait à la main dans la fenêtre).
Ensuite la session est réutilisée. Chrome se ferme à la fin.

### Options de ligne de commande

Toutes facultatives (sans option, le script lit `profiles.csv` et écrit `invitations.csv` comme avant) :

| Option | Rôle |
|---|---|
| `--profiles <fichier>` | CSV d'entrée (`url;note`) |
| `--results <fichier>` | journal de sortie |
| `--max <n>` | nombre maximum d'invitations pour ce lancement |

C'est ce qu'utilise [LinkedIn Agent](../Linkedin%20Agent/README.md) : il écrit la liste du jour dans `state/bot_profiles.csv`,
lance le bot, puis relit `state/bot_results.csv` pour mettre à jour ses contacts.

**Arrêt :** `Ctrl+C` (ou un arrêt envoyé par un autre programme) ferme Chrome proprement ; les résultats déjà obtenus sont conservés.

**Profils où « Suivre » est le bouton principal :** « Se connecter » est alors caché dans le menu « … ». Le bot attend que les boutons
du profil soient affichés, ouvre le menu et réessaie jusqu'à 3 fois si LinkedIn rafraîchit la page, avant de conclure `INDISPONIBLE`.

## Résultats : `invitations.csv`

Une ligne par profil, mise à jour à chaque tentative : `url;nom;statut;note;date`.

| Statut | Signification |
|---|---|
| `ENVOYE` | invitation envoyée (colonne `note` : `avec_note` ou `sans_note`) |
| `EN_ATTENTE` | une invitation était déjà en attente |
| `INDISPONIBLE` | pas de bouton « Se connecter » (déjà connecté, profil restreint, « Suivre » seulement…) |
| `ERREUR` | problème technique, voir ci-dessous |

`ENVOYE` et `EN_ATTENTE` sont ignorés aux lancements suivants ; `INDISPONIBLE` et `ERREUR` sont retentés.
Le script ne sait pas si une invitation a été acceptée ensuite.

## En cas d'erreur (à envoyer au mainteneur)

Quand un profil sort en `ERREUR` ou `INDISPONIBLE`, le script crée **automatiquement, sur la machine
qui l'a lancé**, un dossier `debug/` avec une capture d'écran (`.png`) et le HTML de la page (`.html`,
et `.shadow.html` pour la fenêtre d'invitation). Rien n'est envoyé tout seul : il faut transmettre
ces fichiers, avec le texte affiché dans le terminal.

⚠️ Ces fichiers contiennent des données de **votre** session LinkedIn (votre nom, votre messagerie,
le contenu de la page). Jetez un œil à la capture avant de la partager, et supprimez `debug/` ensuite.

## Fichiers

| Fichier | Rôle |
|---|---|
| `connect_profiles.py` | script principal |
| `linkedin_session.py` | lancement de Chrome et connexion |
| `parameters.py` | identifiants (lus depuis `.env`) et réglages |
| `profiles.example.csv` | modèle du CSV d'entrée |
| `profiles.csv`, `invitations.csv`, `.env`, `.chrome_profile/`, `debug/` | locaux, ignorés par git |
