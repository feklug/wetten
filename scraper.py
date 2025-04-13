import time
import csv
import firebase_admin
from firebase_admin import credentials, firestore
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# === Webdriver Setup ===
def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.headless = False  # Setze auf True, wenn du ohne Browserfenster arbeiten willst
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# === Firestore Setup ===
def init_firestore():
    cred = credentials.Certificate("accelerate-app-f3f90-firebase-adminsdk-mnbwy-917250e91c.json")  # <-- Anpassen!
    firebase_admin.initialize_app(cred)
    return firestore.client()

# === Scraper für Fußball ===
def scrape_football_events(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "s-event"))
    )

    events = driver.find_elements(By.CLASS_NAME, "s-event")
    print(f"⚽ Fußball: {len(events)} Events gefunden.")

    event_data = []

    for event in events:
        try:
            team_names = event.find_elements(By.CLASS_NAME, "s-event-player")
            if len(team_names) < 2:
                continue
            team1 = team_names[0].text.strip()
            team2 = team_names[1].text.strip()

            game_time = event.find_element(By.CLASS_NAME, "s-event-gametime").text.strip()

            odds = event.find_elements(By.CLASS_NAME, "s-outcome-odd")
            if len(odds) >= 3:
                odd1 = odds[0].text.strip()
                oddX = odds[1].text.strip()
                odd2 = odds[2].text.strip()
            else:
                odd1 = oddX = odd2 = "N/A"

            event_data.append([team1, team2, game_time, odd1, oddX, odd2])
        except Exception as e:
            print("⚠️ Fehler bei Fußball-Event:", e)

    return event_data

# === Scraper für Tennis ===
def scrape_tennis_events(driver, url):
    driver.get(url)
    WebDriverWait(driver, 10).until(
        EC.presence_of_element_located((By.CLASS_NAME, "s-event"))
    )

    events = driver.find_elements(By.CLASS_NAME, "s-event")
    print(f"🎾 Tennis: {len(events)} Events gefunden.")

    tennis_data = []

    for event in events:
        try:
            players = event.find_elements(By.CLASS_NAME, "s-event-player")
            if len(players) < 2:
                continue
            player1 = players[0].text.strip()
            player2 = players[1].text.strip()

            game_time = event.find_element(By.CLASS_NAME, "s-event-gametime").text.strip()

            odds = event.find_elements(By.CLASS_NAME, "s-outcome-odd")
            if len(odds) >= 2:
                odd1 = odds[0].text.strip()
                odd2 = odds[1].text.strip()
            else:
                odd1 = odd2 = "N/A"

            tennis_data.append([player1, player2, game_time, odd1, odd2])
        except Exception as e:
            print("⚠️ Fehler bei Tennis-Event:", e)

    return tennis_data

# === Arbitrage-Erkennung ===
def find_arbitrage_opportunities(data, is_tennis=False):
    arbitrage = []
    for row in data:
        try:
            odds = list(map(lambda x: float(x.replace(",", ".")) if x != "N/A" else None, row[3:]))
            if None in odds:
                continue

            if is_tennis and len(odds) == 2:
                total = 1/odds[0] + 1/odds[1]
            elif not is_tennis and len(odds) == 3:
                total = 1/odds[0] + 1/odds[1] + 1/odds[2]
            else:
                continue

            if total < 1:
                row.append(round(total, 3))  # Arbitrage-Wert
                arbitrage.append(row)
        except Exception as e:
            print("⚠️ Fehler bei Arbitrage-Prüfung:", e)
    return arbitrage

# === CSV Export ===
def save_to_csv(data, filename, is_tennis=False):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        if is_tennis:
            writer.writerow(["Team 1", "Team 2", "Spielzeit", "1", "2"])
        else:
            writer.writerow(["Team 1", "Team 2", "Spielzeit", "1", "X", "2"])
        for row in data:
            writer.writerow(row)
    print(f"💾 Gespeichert in '{filename}'.")

# === Firestore Export ===
def save_arbitrage_to_firestore(db, data, collection_name, is_tennis=False):
    collection = db.collection(collection_name)
    for row in data:
        doc = {
            "team1": row[0],
            "team2": row[1],
            "spielzeit": row[2],
            "quote1": row[3],
            "quoteX": row[4] if not is_tennis else None,
            "quote2": row[4] if is_tennis else row[5],
            "arbitrage_wert": row[-1],
            "timestamp": firestore.SERVER_TIMESTAMP,
        }
        collection.add(doc)
    print(f"🔥 {len(data)} Arbitrage-Fälle in Firestore gespeichert ({collection_name}).")

# === Main-Programm ===
def main():
    driver = init_driver()
    db = init_firestore()

    try:
        football_url = "https://www.interwetten.com/de/sportwetten/heute"
        tennis_url = "https://www.interwetten.com/de/sportwetten/heute/11"

        football_data = scrape_football_events(driver, football_url)
        if football_data:
            save_to_csv(football_data, "interwetten_fussball.csv")
            arbitrage_fussball = find_arbitrage_opportunities(football_data, is_tennis=False)
            if arbitrage_fussball:
                save_arbitrage_to_firestore(db, arbitrage_fussball, "arbitrage_fussball")

        tennis_data = scrape_tennis_events(driver, tennis_url)
        if tennis_data:
            save_to_csv(tennis_data, "interwetten_tennis.csv", is_tennis=True)
            arbitrage_tennis = find_arbitrage_opportunities(tennis_data, is_tennis=True)
            if arbitrage_tennis:
                save_arbitrage_to_firestore(db, arbitrage_tennis, "arbitrage_tennis")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
