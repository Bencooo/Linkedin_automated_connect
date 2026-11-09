"""Envoie une invitation LinkedIn (avec la note du CSV si elle existe, sinon sans note) à chaque profil listé dans profiles.csv (colonnes url;note).

Lancer : python connect_profiles.py
La connexion et la session Chrome persistante viennent de linkedin_session.py.
"""
import csv
import random
import re
import time
from datetime import datetime
from pathlib import Path

from selenium.common.exceptions import ElementClickInterceptedException
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait

import parameters
from linkedin_session import build_driver, login

CONNECT_LABELS = {"se connecter", "connect"}
PENDING_LABELS = {"en attente", "pending"}
MORE_LABELS = ("plus", "more")  # préfixes de l'aria-label du bouton « … » (« Plus d'actions », « More actions »)
ADD_NOTE_LABELS = {"ajouter une note", "add a note"}
SEND_NO_NOTE_LABELS = {"envoyer sans note", "send without a note", "envoyer", "send"}
SEND_LABELS = {"envoyer", "send"}
NOTE_MAX_CHARS = 300  # limite LinkedIn

DEBUG_DIR = Path(__file__).resolve().parent / "debug"
SENT, PENDING, UNAVAILABLE, ERROR = "ENVOYE", "EN_ATTENTE", "INDISPONIBLE", "ERREUR"
WITH_NOTE, WITHOUT_NOTE = "avec_note", "sans_note"
RESULT_COLUMNS = ["url", "nom", "statut", "note", "date"]


def norm(text):
    return (text or "").replace("’", "'").strip().lower()


def read_profiles(path):
    """Lit profiles.csv (url;note). Retourne une liste de (url, note), sans doublons d'url."""
    with open(path, newline="", encoding="utf-8-sig") as f:
        rows = csv.DictReader(f, delimiter=";")
        if not rows.fieldnames or "url" not in [c.strip().lower() for c in rows.fieldnames]:
            raise RuntimeError(f"{path} doit avoir un en-tête avec au moins la colonne « url » (url;note)")
        profiles = {}
        for row in rows:
            row = {(k or "").strip().lower(): (v or "").strip() for k, v in row.items()}
            if row.get("url") and not row["url"].startswith("#"):
                profiles.setdefault(row["url"], row.get("note", ""))
    return list(profiles.items())


def already_done(path):
    """URLs déjà invitées (envoyées ou en attente) d'après le journal."""
    if not Path(path).exists():
        return set()
    with open(path, newline="", encoding="utf-8") as f:
        return {r["url"] for r in csv.DictReader(f, delimiter=";") if r.get("statut") in (SENT, PENDING)}


def log_result(path, url, name, status, note_mode):
    """Une seule ligne par profil : on met à jour la ligne existante au lieu d'en ajouter une."""
    rows = {}
    if Path(path).exists():
        with open(path, newline="", encoding="utf-8") as f:
            rows = {r["url"]: r for r in csv.DictReader(f, delimiter=";") if r.get("url")}
    previous = rows.get(url, {})
    rows[url] = {
        "url": url,
        "nom": name or previous.get("nom", ""),
        "statut": status,
        "note": note_mode,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M"),
    }
    with open(path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=RESULT_COLUMNS, delimiter=";")
        writer.writeheader()
        writer.writerows(rows.values())


def visible(el):
    return el.is_displayed() and el.is_enabled()


def profile_name(driver):
    """Nom lu dans le titre de l'onglet (« Thibaud Texier | LinkedIn », parfois préfixé par « (23) »)."""
    def read_title(d):
        title = re.sub(r"^\(\d+\)\s*", "", d.title or "")
        return title.split("|")[0].strip() if "|" in title else False
    return WebDriverWait(driver, 15).until(read_title)


def safe_click(driver, el):
    """Clic normal, ou clic JavaScript si un bandeau/popup recouvre l'élément."""
    driver.execute_script("arguments[0].scrollIntoView({block: 'center'});", el)
    try:
        el.click()
    except ElementClickInterceptedException:
        driver.execute_script("arguments[0].click();", el)


def dump_debug(driver, url):
    """Sauvegarde une capture et le HTML de la page pour comprendre une erreur."""
    DEBUG_DIR.mkdir(exist_ok=True)
    slug = re.sub(r"[^a-z0-9]+", "-", url.lower()).strip("-")[-60:]
    driver.save_screenshot(str(DEBUG_DIR / f"{slug}.png"))
    (DEBUG_DIR / f"{slug}.html").write_text(driver.page_source, encoding="utf-8")
    shadow_html = driver.execute_script(
        "const h = document.querySelector('#interop-outlet'); return h && h.shadowRoot ? h.shadowRoot.innerHTML : '';")
    if shadow_html:
        (DEBUG_DIR / f"{slug}.shadow.html").write_text(shadow_html, encoding="utf-8")
    print(f"  capture et HTML sauvegardés dans {DEBUG_DIR / slug}.*")


def aria_text(el):
    """aria-label de l'élément et de ses descendants (dans le menu « … », il est sur un <div> interne)."""
    labels = [el.get_attribute("aria-label")] + [c.get_attribute("aria-label") for c in el.find_elements(By.CSS_SELECTOR, "[aria-label]")]
    return norm(" ".join(l for l in labels if l))


def page_scope(driver):
    """Zone de la page à explorer : <main> s'il existe, sinon toute la page."""
    return "main " if driver.find_elements(By.CSS_SELECTOR, "main") else ""


def find_for_person(driver, labels, name, tags="button, a", scope=None):
    """Élément visible au libellé exact ET dont l'aria-label contient le nom du profil.

    Le contrôle du nom évite de cliquer « Se connecter » sur les suggestions
    « Autres profils consultés » affichées sur la même page.
    """
    scope = page_scope(driver) if scope is None else scope
    for el in driver.find_elements(By.CSS_SELECTOR, ", ".join(scope + t.strip() for t in tags.split(","))):
        if visible(el) and norm(el.text) in labels and name in aria_text(el):
            return el
    return None


def dialog_elements(driver, css):
    """Éléments `css` à l'intérieur de la fenêtre d'invitation ([role="dialog"]).

    LinkedIn affiche cette fenêtre dans un shadow DOM (#interop-outlet), invisible dans le
    HTML normal : on cherche d'abord là, puis dans la page. Liste vide si la fenêtre n'est pas affichée.
    """
    scopes = []
    try:
        scopes = [host.shadow_root for host in driver.find_elements(By.CSS_SELECTOR, "#interop-outlet")]
    except Exception:
        pass
    for scope in scopes + [driver]:
        try:
            found = scope.find_elements(By.CSS_SELECTOR, f'[role="dialog"] {css}')
            if found:
                return found
        except Exception:
            continue
    return []


def click_in_dialog(driver, labels, timeout=8):
    """Attend un bouton de la fenêtre au libellé exact, puis le clique. False si absent."""
    def find(d):
        try:
            return next((b for b in dialog_elements(d, "button") if visible(b) and norm(b.text) in labels), False)
        except Exception:
            return False
    try:
        button = WebDriverWait(driver, timeout).until(find)
    except Exception:
        return False
    safe_click(driver, button)
    return True


def wait_dialog_closed(driver, timeout=6):
    try:
        WebDriverWait(driver, timeout).until(lambda d: not dialog_elements(d, "button"))
    except Exception:
        pass


def send_with_note(driver, note):
    """Ajoute la note puis envoie. Lève une exception si ce n'est pas possible."""
    if not click_in_dialog(driver, ADD_NOTE_LABELS):
        raise RuntimeError("bouton « Ajouter une note » indisponible")
    textarea = WebDriverWait(driver, 5).until(lambda d: next(iter(dialog_elements(d, "textarea")), False))
    textarea.send_keys(note[:NOTE_MAX_CHARS])
    if not click_in_dialog(driver, SEND_LABELS):
        raise RuntimeError("bouton « Envoyer » introuvable après la note")
    wait_dialog_closed(driver)


def send_without_note(driver):
    if not click_in_dialog(driver, SEND_NO_NOTE_LABELS):
        raise RuntimeError("bouton « Envoyer sans note » introuvable dans la fenêtre (email requis ?)")
    wait_dialog_closed(driver)


def open_connect_dialog(driver, url):
    """Ouvre le profil et la fenêtre d'invitation. Retourne (statut, prénom) ; statut None = fenêtre ouverte."""
    driver.get(url)
    full_name = profile_name(driver)
    first_name = norm(full_name.split()[0])

    if find_for_person(driver, PENDING_LABELS, first_name):
        return PENDING, full_name

    button = find_for_person(driver, CONNECT_LABELS, first_name)
    if not button:
        # Parfois « Se connecter » est caché dans le menu « Plus »
        # Le bouton « … » n'a pas de texte (icône) : on lit son aria-label.
        more = next((b for b in driver.find_elements(By.CSS_SELECTOR, page_scope(driver) + "button")
                     if visible(b) and norm(b.get_attribute("aria-label")).startswith(MORE_LABELS)), None)
        if more:
            safe_click(driver, more)
            time.sleep(1)
            button = find_for_person(driver, CONNECT_LABELS, first_name,
                                     tags='[role="menuitem"], div[role="button"], a, button', scope="")
    if not button:
        return UNAVAILABLE, full_name  # déjà connecté, « Suivre » seulement, profil restreint…

    safe_click(driver, button)
    return None, full_name


def connect_to(driver, url, note):
    """Retourne (statut, nom, avec/sans note). Lève une exception en cas de problème."""
    status, full_name = open_connect_dialog(driver, url)
    if status:
        return status, full_name, ""

    if note:
        try:
            send_with_note(driver, note)
            time.sleep(2)
            return SENT, full_name, WITH_NOTE
        except Exception as e:
            print(f"  note impossible ({e}), nouvel essai sans note")
            status, _ = open_connect_dialog(driver, url)  # on repart d'un état propre
            if status:
                return status, full_name, ""
    send_without_note(driver)
    time.sleep(2)
    return SENT, full_name, WITHOUT_NOTE


def main():
    profiles_path = Path(parameters.profiles_file)
    if not profiles_path.exists():
        print(f"ERREUR : crée {profiles_path} (voir profiles.example.csv) avec les colonnes url;note.")
        return

    done = already_done(parameters.results_file)
    todo = [(u, n) for u, n in read_profiles(profiles_path) if u not in done]
    print(f"{len(todo)} profil(s) à traiter (limite : {parameters.max_invites_per_run} invitations).")
    if not todo:
        return

    driver = None
    sent = 0
    crashed = False
    try:
        driver = build_driver()
        login(driver)
        for i, (url, note) in enumerate(todo):
            if sent >= parameters.max_invites_per_run:
                print("Limite par lancement atteinte, arrêt.")
                break
            name, note_mode = "", ""
            try:
                status, name, note_mode = connect_to(driver, url, note)
            except Exception as e:
                status = ERROR
                print(f"  détail : {type(e).__name__}: {e}".splitlines()[0])
                try:
                    dump_debug(driver, url)
                except Exception:
                    pass
            if status == UNAVAILABLE:
                try:
                    dump_debug(driver, url)
                except Exception:
                    pass
            log_result(parameters.results_file, url, name, status, note_mode)
            print(f"{status:12} {note_mode:10} {name or url}")
            if status == SENT:
                sent += 1
            is_last = i == len(todo) - 1
            if not is_last and sent < parameters.max_invites_per_run:
                time.sleep(random.uniform(parameters.min_delay_seconds, parameters.max_delay_seconds))
        print(f"Terminé : {sent} invitation(s) envoyée(s).")
    except KeyboardInterrupt:
        print("\nINFO : annulé par l'utilisateur")
    except Exception as e:
        crashed = True
        print(f"ERREUR : {e}")
    finally:
        if driver:
            if crashed:  # erreur inattendue : on laisse Chrome ouvert pour inspecter
                input("Chrome reste ouvert pour inspection. Appuie sur Entrée pour fermer.")
            driver.quit()


if __name__ == "__main__":
    main()
