import time
import csv
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager

# Initialisiere Webdriver
def init_driver():
    options = Options()
    options.add_argument("--disable-gpu")
    options.headless = False  # Setze auf True, um im Hintergrund zu scrapen
    service = Service(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=options)
    return driver

# Fußball Scraper
def scrape_football_bwin(driver, url):
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "grid-event-wrapper"))
    )
    events = driver.find_elements(By.CLASS_NAME, "grid-event-wrapper")
    print(f"⚽ Fußball: {len(events)} Events gefunden.")

    data = []
    for event in events:
        try:
            team_elements = event.find_elements(By.CLASS_NAME, "participant")
            if len(team_elements) < 2:
                continue
            team1 = team_elements[0].text.strip()
            team2 = team_elements[1].text.strip()

            try:
                game_time = event.find_element(By.CLASS_NAME, "ms-live-timer").text.strip()
            except:
                game_time = "N/A"

            odds_elements = event.find_elements(By.CLASS_NAME, "option-value")
            if len(odds_elements) >= 3:
                odd1 = odds_elements[0].text.strip()
                oddX = odds_elements[1].text.strip()
                odd2 = odds_elements[2].text.strip()
            else:
                odd1 = oddX = odd2 = "N/A"

            data.append([team1, team2, game_time, odd1, oddX, odd2])
        except Exception as e:
            print("⚠️ Fehler beim Parsen eines Fußball-Events:", e)
    return data

# Tennis Scraper (ohne Unentschieden)
def scrape_tennis_bwin(driver, url):
    driver.get(url)
    WebDriverWait(driver, 20).until(
        EC.presence_of_element_located((By.CLASS_NAME, "grid-event-wrapper"))
    )
    events = driver.find_elements(By.CLASS_NAME, "grid-event-wrapper")
    print(f"🎾 Tennis: {len(events)} Events gefunden.")

    data = []
    for event in events:
        try:
            player_elements = event.find_elements(By.CLASS_NAME, "participant")
            if len(player_elements) < 2:
                continue
            player1 = player_elements[0].text.strip()
            player2 = player_elements[1].text.strip()

            try:
                time_element = event.find_element(By.CLASS_NAME, "starting-time")
                game_time = time_element.text.strip()
            except:
                game_time = "N/A"

            odds_elements = event.find_elements(By.CLASS_NAME, "option-value")
            if len(odds_elements) >= 2:
                odd1 = odds_elements[0].text.strip()
                odd2 = odds_elements[1].text.strip()
            else:
                odd1 = odd2 = "N/A"

            data.append([player1, player2, game_time, odd1, odd2])
        except Exception as e:
            print("⚠️ Fehler bei einem Tennis-Event:", e)
    return data

# CSV-Speicherfunktion
def save_to_csv(data, filename="bwin_wetten.csv", is_tennis=False):
    with open(filename, mode="w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        if is_tennis:
            writer.writerow(["Spieler 1", "Spieler 2", "Spielzeit", "1", "2"])
        else:
            writer.writerow(["Team 1", "Team 2", "Spielzeit", "1", "X", "2"])
        for row in data:
            writer.writerow(row)
    print(f"✅ Daten gespeichert in '{filename}'.")

# Hauptfunktion
def main():
    driver = init_driver()
    try:
        # Fußball-URL
        football_url = "https://sports.bwin.com/de-at/sports/fu%C3%9Fball-4/heute"
        football_data = scrape_football_bwin(driver, football_url)
        if football_data:
            save_to_csv(football_data, "bwin_fussball.csv")
        else:
            print("⚠️ Keine Fußball-Events gefunden.")

        # Tennis-URL
        tennis_url = "https://sports.bwin.com/de-at/sports/tennis-5/heute"
        tennis_data = scrape_tennis_bwin(driver, tennis_url)
        if tennis_data:
            save_to_csv(tennis_data, "bwin_tennis.csv", is_tennis=True)
        else:
            print("⚠️ Keine Tennis-Events gefunden.")

    finally:
        driver.quit()

if __name__ == "__main__":
    main()
