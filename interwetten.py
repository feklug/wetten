import time
import csv
import tempfile
import os
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Setup des Webdrivers


def init_driver():
    options = webdriver.ChromeOptions()
    options.add_argument("--disable-gpu")
    options.headless = True  # True für headless, False um Browser sichtbar zu machen

    # Erstelle ein temporäres Verzeichnis für das User-Datenverzeichnis
    user_data_dir = tempfile.mkdtemp()  # Ein einzigartiges temporäres Verzeichnis
    options.add_argument(f"user-data-dir={user_data_dir}")

    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver


# Scraper für Fußball
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

# Scraper für Tennis (ohne Unentschieden)
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

# Speichern als CSV für Tennis
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


# Hauptprogramm
def main():
    driver = init_driver()
    try:
        football_url = "https://www.interwetten.com/de/sportwetten/heute"
        tennis_url = "https://www.interwetten.com/de/sportwetten/heute/11"

        football_data = scrape_football_events(driver, football_url)
        if football_data:
            save_to_csv(football_data, "interwetten_fussball.csv")

        tennis_data = scrape_tennis_events(driver, tennis_url)
        if tennis_data:
            save_to_csv(tennis_data, "interwetten_tennis.csv")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
