"""Envoie une invitation LinkedIn (sans note) à chaque profil listé dans profiles.txt.

Lancer : python connect_profiles.py
La connexion et la session Chrome persistante viennent de linkedIn.py.
"""
import csv
import random
import time
from datetime import datetime
from pathlib import Path

from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import parameters
from linkedIn import build_driver, login

CONNECT_LABELS = {"se connecter", "connect"}
PENDING_LABELS = {"en attente", "pending"}
MORE_LABELS = {"plus", "more"}
SEND_LABELS = {"envoyer sans note", "send without a note", "envoyer", "send"}

SENT, PENDING, UNAVAILABLE, ERROR = "ENVOYE", "EN_ATTENTE", "INDISPONIBLE", "ERREUR"


def norm(text):
    return (text or "").replace("’", "'").strip().lower()


def read_profiles(path):
    lines = Path(path).read_text(encoding="utf-8").splitlines()
    urls = [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    return list(dict.fromkeys(urls))  # dédoublonne en gardant l'ordre


def already_sent(path):
    if not Path(path).exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {row[0] for row in csv.reader(f, delimiter=";") if len(row) >= 2 and row[1] in (SENT, PENDING)}


def log_result(path, url, status):
    with open(path, "a", newline="", encoding="utf-8") as f:
        csv.writer(f, delimiter=";").writerow([url, status, datetime.now().strftime("%Y-%m-%d %H:%M")])


def visible(el):
    return el.is_displayed() and el.is_enabled()


def profile_name(driver):
    return norm(WebDriverWait(driver, 15).until(lambda d: d.find_element(By.CSS_SELECTOR, "main h1")).text)


def find_for_person(driver, labels, name, tags="button, a", scope="main "):
    """Élément visible au libellé exact ET dont l'aria-label contient le nom du profil.

    Le contrôle du nom évite de cliquer « Se connecter » sur les suggestions
    « Autres profils consultés » affichées sur la même page.
    """
    for el in driver.find_elements(By.CSS_SELECTOR, ", ".join(scope + t.strip() for t in tags.split(","))):
        if visible(el) and norm(el.text) in labels and name in norm(el.get_attribute("aria-label")):
            return el
    return None


def click_send_in_dialog(driver):
    dialog = WebDriverWait(driver, 10).until(lambda d: d.find_element(By.CSS_SELECTOR, '[role="dialog"]'))
    for btn in dialog.find_elements(By.CSS_SELECTOR, "button"):
        if visible(btn) and norm(btn.text) in SEND_LABELS:
            btn.click()
            return
    raise RuntimeError("bouton « Envoyer sans note » introuvable dans la fenêtre (email requis ?)")


def connect_to(driver, url):
    """Retourne le statut (SENT, PENDING, UNAVAILABLE) ; lève une exception en cas de problème."""
    driver.get(url)
    name = profile_name(driver)
    first_name = name.split()[0] if name else name

    if find_for_person(driver, PENDING_LABELS, first_name):
        return PENDING

    button = find_for_person(driver, CONNECT_LABELS, first_name)
    if not button:
        # Parfois « Se connecter » est caché dans le menu « Plus »
        more = next((b for b in driver.find_elements(By.CSS_SELECTOR, "main button")
                     if visible(b) and norm(b.text) in MORE_LABELS), None)
        if more:
            more.click()
            time.sleep(1)
            button = find_for_person(driver, CONNECT_LABELS, first_name, tags='[role="menuitem"], div[role="button"], a, button', scope="")
    if not button:
        return UNAVAILABLE  # déjà connecté, « Suivre » seulement, profil restreint…

    button.click()
    click_send_in_dialog(driver)
    time.sleep(2)
    return SENT


def main():
    profiles_path = Path(parameters.profiles_file)
    if not profiles_path.exists():
        print(f"ERREUR : crée {profiles_path} (voir profiles.example.txt), un lien par ligne.")
        return

    done = already_sent(parameters.results_file)
    todo = [u for u in read_profiles(profiles_path) if u not in done]
    print(f"{len(todo)} profil(s) à traiter (limite : {parameters.max_invites_per_run} invitations).")
    if not todo:
        return

    driver = None
    sent = 0
    try:
        driver = build_driver()
        login(driver)
        for url in todo:
            if sent >= parameters.max_invites_per_run:
                print("Limite par lancement atteinte, arrêt.")
                break
            try:
                status = connect_to(driver, url)
            except Exception as e:
                status = ERROR
                print(f"  détail : {e}")
            log_result(parameters.results_file, url, status)
            print(f"{status:12} {url}")
            if status == SENT:
                sent += 1
            time.sleep(random.uniform(parameters.min_delay_seconds, parameters.max_delay_seconds))
        print(f"Terminé : {sent} invitation(s) envoyée(s).")
    except KeyboardInterrupt:
        print("\nINFO : annulé par l'utilisateur")
    except Exception as e:
        print(f"ERREUR : {e}")
    finally:
        if driver:
            input("Appuie sur Entrée pour fermer Chrome.")
            driver.quit()


if __name__ == "__main__":
    main()
