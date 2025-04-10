import pandas as pd
from fuzzywuzzy import fuzz
import re
import firebase_admin
from firebase_admin import credentials, firestore

# Firebase initialisieren
cred = credentials.Certificate("accelerate-app-f3f90-firebase-adminsdk-mnbwy-917250e91c.json")  # Pfad zu deiner JSON-Datei
firebase_admin.initialize_app(cred)
db = firestore.client()

# CSV-Dateien laden
def load_csv(filename):
    df = pd.read_csv(filename)
    df["source"] = filename.split("_")[0]  # z. B. interwetten
    return df

# Teamnamen vereinheitlichen
def normalize_team_name(name):
    name = re.sub(r"\b(FC|Borussia)\b", "", name, flags=re.IGNORECASE)
    name = name.strip().lower()
    return name

# Funktion zum Vergleichen von Teams (auch bei vertauschter Reihenfolge)
def is_match(t1a, t2a, t1b, t2b):
    t1a = normalize_team_name(t1a)
    t2a = normalize_team_name(t2a)
    t1b = normalize_team_name(t1b)
    t2b = normalize_team_name(t2b)
    
    score_normal = fuzz.token_sort_ratio(t1a, t1b) + fuzz.token_sort_ratio(t2a, t2b)
    score_swapped = fuzz.token_sort_ratio(t1a, t2b) + fuzz.token_sort_ratio(t2a, t1b)
    
    return max(score_normal, score_swapped) / 2 >= 85

# CSV-Dateien laden
interwetten = load_csv("interwetten_fussball.csv")
bwin = load_csv("bwin_fussball.csv")
betathome = load_csv("betathome_wetten.csv")

all_data = pd.concat([interwetten, bwin, betathome], ignore_index=True)

# Spiele gruppieren
groups = []
used = set()

for i, row1 in all_data.iterrows():
    if i in used:
        continue
    group = [row1]
    used.add(i)
    for j, row2 in all_data.iterrows():
        if j in used or i == j:
            continue
        if is_match(row1["Team 1"], row1["Team 2"], row2["Team 1"], row2["Team 2"]):
            group.append(row2)
            used.add(j)
    if len(group) == 3:
        groups.append(group)

# Arbitrage Berechnung
def calculate_arbitrage(odds):
    return sum(1 / float(odd) for odd in odds if odd != "N/A")

# Hauptverarbeitung
arbitrage_results = []
einsatz_total = 100.0

print("\n🔍 DEBUG: Alle Spiele mit Quoten von allen drei Anbietern\n")

for group in groups:
    team1 = group[0]["Team 1"]
    team2 = group[0]["Team 2"]
    print(f"📊 Spiel: {team1} vs {team2}")

    quotes = {}
    for bet in group:
        quotes[bet["source"]] = {
            "1": bet["1"],
            "X": bet["X"],
            "2": bet["2"]
        }

    for source, q in quotes.items():
        print(f"  {source}: 1 = {q['1']}, X = {q['X']}, 2 = {q['2']}")

    best_1 = max((r for r in group if r["1"] != "N/A"), key=lambda x: float(x["1"]), default=None)
    best_X = max((r for r in group if r["X"] != "N/A"), key=lambda x: float(x["X"]), default=None)
    best_2 = max((r for r in group if r["2"] != "N/A"), key=lambda x: float(x["2"]), default=None)

    if best_1 is not None and best_X is not None and best_2 is not None:
        q1 = float(best_1["1"])
        qX = float(best_X["X"])
        q2 = float(best_2["2"])
        arb_sum = calculate_arbitrage([q1, qX, q2])

        if arb_sum < 1:
            e1 = (einsatz_total / q1) / arb_sum
            eX = (einsatz_total / qX) / arb_sum
            e2 = (einsatz_total / q2) / arb_sum
            payout = round(e1 * q1, 2)
            profit = round(payout - einsatz_total, 2)

            print(f"  ✅ Arbitrage möglich! (Summe: {round(arb_sum, 4)} < 1)")
            print(f"     1 - Quote: {q1} ({best_1['source']}), Einsatz: {round(e1, 2)}€")
            print(f"     X - Quote: {qX} ({best_X['source']}), Einsatz: {round(eX, 2)}€")
            print(f"     2 - Quote: {q2} ({best_2['source']}), Einsatz: {round(e2, 2)}€")
            print(f"     📈 Auszahlung: {payout}€, Gewinn: {profit}€\n")

            result = {
                "Team 1": team1,
                "Team 2": team2,
                "Quote 1": q1,
                "Quelle 1": best_1["source"],
                "Einsatz 1": round(e1, 2),
                "Quote X": qX,
                "Quelle X": best_X["source"],
                "Einsatz X": round(eX, 2),
                "Quote 2": q2,
                "Quelle 2": best_2["source"],
                "Einsatz 2": round(e2, 2),
                "Gesamteinsatz": einsatz_total,
                "Auszahlung": payout,
                "Gewinn": profit,
                "Arbitrage Summe": round(arb_sum, 4)
            }

            arbitrage_results.append(result)

            # 🔥 In Firebase Firestore speichern
            db.collection("arbitrage_bets").add(result)

        else:
            print(f"  ❌ Keine Arbitrage möglich. (Summe: {round(arb_sum, 4)} ≥ 1)\n")

# Lokale CSV speichern (optional)
if arbitrage_results:
    df_out = pd.DataFrame(arbitrage_results)
    df_out.to_csv("arbitrage_ergebnisse.csv", index=False, encoding="utf-8-sig")
    print("✅ Ergebnisse gespeichert in 'arbitrage_ergebnisse.csv'")
else:
    print("❌ Keine Arbitrage-Möglichkeiten gefunden.")
