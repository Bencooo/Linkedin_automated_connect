from pathlib import Path

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

import parameters

# NOTE : la recherche et l'envoi d'invitations (open_profile, search_and_send_request,
# log CSV, ignore_list) sont volontairement désactivés. Ils restent disponibles dans
# l'historique git (commit 21a38db) et ne doivent pas être réactivés pour l'instant.

LOGIN_URL = "https://www.linkedin.com/login"
FEED_URL = "https://www.linkedin.com/feed/"
# Profil Chrome dédié : conserve les cookies entre deux lancements (pas besoin de se reconnecter).
PROFILE_DIR = Path(__file__).resolve().parent / ".chrome_profile"
WAIT_SECONDS = 15

# Libellés exacts acceptés pour le bouton de connexion (comparaison stricte, pas de sous-chaîne,
# sinon "Sign in with Passkey" / Apple serait cliqué).
LOGIN_LABELS = {"s'identifier", "se connecter", "sign in", "log in"}
# Boutons à ignorer absolument.
BLOCKED_WORDS = ("apple", "passkey", "google", "facebook", "microsoft", "afficher")


def _normalize(text):
    return (text or "").replace("’", "'").strip().lower()


def visible_input(driver, css_selector):
    """Premier élément visible et actif correspondant au sélecteur (ignore les champs cachés)."""
    for el in driver.find_elements(By.CSS_SELECTOR, css_selector):
        if el.is_displayed() and el.is_enabled():
            return el
    return False


def linkedin_login_button(driver):
    """Bouton de connexion LinkedIn (type="button", libellé exact), ou False."""
    for el in driver.find_elements(By.CSS_SELECTOR, 'button[type="button"]'):
        if not (el.is_displayed() and el.is_enabled()):
            continue
        label = _normalize(el.text)
        combined = f"{label} {_normalize(el.get_attribute('aria-label'))}"
        if any(word in combined for word in BLOCKED_WORDS):
            continue
        if label in LOGIN_LABELS:
            return el
    return False


def fill_field(driver, css_selector, value, name):
    try:
        field = WebDriverWait(driver, WAIT_SECONDS).until(lambda d: visible_input(d, css_selector))
    except Exception:
        raise RuntimeError(f"Champ « {name} » introuvable ou non visible ({css_selector})")
    field.click()
    field.send_keys(value)


def build_driver():
    options = Options()
    options.add_argument(f"--user-data-dir={PROFILE_DIR}")
    return webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)


def is_logged_in(driver):
    """Vrai si LinkedIn ouvre le fil d'actualité sans rediriger vers login/authwall."""
    driver.get(FEED_URL)
    url = driver.current_url
    return "/feed" in url and not any(x in url for x in ("login", "authwall", "checkpoint"))


def login(driver):
    """Se connecte avec les identifiants du .env, sauf si la session est déjà active."""
    if is_logged_in(driver):
        print("Session déjà active, connexion ignorée.")
        return

    if not parameters.linkedin_username or not parameters.linkedin_password:
        raise RuntimeError("Identifiants manquants : renseigne LINKEDIN_USERNAME et LINKEDIN_PASSWORD dans .env")

    driver.get(LOGIN_URL)
    # Les id sont dynamiques et il y a des champs cachés : on cible le type, en visible.
    fill_field(driver, 'input[type="email"]', parameters.linkedin_username, "email")
    fill_field(driver, 'input[type="password"]', parameters.linkedin_password, "mot de passe")

    try:
        button = WebDriverWait(driver, WAIT_SECONDS).until(linkedin_login_button)
    except Exception:
        raise RuntimeError("Bouton de connexion introuvable (S'identifier / Se connecter / Sign in / Log in)")
    print("Bouton cliqué :", repr(button.text))
    button.click()


def main():
    driver = None
    try:
        driver = build_driver()
        login(driver)
        input("Connexion tentée. Appuie sur Entrée dans le terminal pour fermer Chrome.")
    except KeyboardInterrupt:
        print("\nINFO : annulé par l'utilisateur")
    except Exception as e:
        print(f"ERREUR : {e}")
        if driver:
            input("Chrome reste ouvert pour inspection. Appuie sur Entrée pour fermer.")
    finally:
        if driver:
            driver.quit()


if __name__ == "__main__":
    main()
