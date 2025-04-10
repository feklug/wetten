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
    options.headless = False  # True für headless, False um Browser sichtbar zu machen
    
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    
    return driver

# Scrape-Funktion für bet-at-home
def scrape_events(driver, url):
    driver.get(url)

    # Warte initial auf Events oder Button
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "EventItem"))
    )

    # Klicke so lange auf "Mehr anzeigen", wie der Button existiert
    while True:
        try:
            mehr_button = WebDriverWait(driver, 5).until(
                EC.element_to_be_clickable((By.CLASS_NAME, "MatchList__MainButton"))
            )
            print("🔁 Klicke auf 'Mehr anzeigen'...")
            driver.execute_script("arguments[0].click();", mehr_button)
            time.sleep(2)  # kleine Pause, um das Nachladen zu ermöglichen
        except:
            print("✅ Alle Events geladen.")
            break  # Kein Button mehr da – fertig mit Nachladen

    # Nun alle geladenen Events extrahieren
    events = driver.find_elements(By.CLASS_NAME, "EventItem")
    print(f"{len(events)} Events gefunden.")

    event_data = []

    for event in events:
        try:
            team1 = event.find_element(By.CLASS_NAME, "Details__Participant--Home").text.strip()
            team2 = event.find_element(By.CLASS_NAME, "Details__Participant--Away").text.strip()

            try:
                time_part = event.find_element(By.CLASS_NAME, "MatchTime__InfoPart--Time").text.strip()
            except:
                time_part = "N/A"

            odds_buttons = event.find_elements(By.CLASS_NAME, "OddsButton")
            if len(odds_buttons) >= 3:
                odd1 = odds_buttons[0].find_element(By.CLASS_NAME, "OddsButton__Odds").text.strip()
                oddX = odds_buttons[1].find_element(By.CLASS_NAME, "OddsButton__Odds").text.strip()
                odd2 = odds_buttons[2].find_element(By.CLASS_NAME, "OddsButton__Odds").text.strip()
            else:
                odd1 = oddX = odd2 = "N/A"

            event_data.append([team1, team2, time_part, odd1, oddX, odd2])

        except Exception as e:
            print("⚠️ Fehler beim Parsen eines Events:", e)

    return event_data


   
# Speichern in CSV
def save_to_csv(event_data, filename="betathome_wetten.csv"):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["Team 1", "Team 2", "Spielzeit", "1", "X", "2"])
        for row in event_data:
            writer.writerow(row)
    print(f"✅ Daten gespeichert in '{filename}'.")

# Hauptprogramm
def main():
    url = "https://sports2.bet-at-home.com/de"
    driver = init_driver()

    try:
        event_data = scrape_events(driver, url)
        if event_data:
            save_to_csv(event_data)
        else:
            print("Keine Events gefunden.")
    finally:
        driver.quit()

if __name__ == "__main__":
    main()
