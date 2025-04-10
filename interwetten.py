import time
import csv
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
    options.add_argument("--headless")  # Headless-Browser für GitHub Action
    options.add_argument("--no-sandbox")  # Wichtige Option, wenn der Chrome im Container läuft
    options.add_argument("--disable-dev-shm-usage")  # Speicherproblem im Container verhindern
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

# Speichern als CSV für Fußball
def save_to_csv(data, filename):
    with open(filename, mode="w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["Team 1", "Team 2", "Spielzeit", "1", "X", "2"])
        for row in data:
            writer.writerow(row)
    print(f"💾 Gespeichert in '{filename}'.")


# Hauptprogramm
def main():
    driver = init_driver()
    try:
        football_url = "https://www.interwetten.com/de/sportwetten/heute"

        football_data = scrape_football_events(driver, football_url)
        if football_data:
            save_to_csv(football_data, "interwetten_fussball.csv")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()

