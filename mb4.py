#First Bot
import requests
import time
import json
import os
import random

# =============================
# CONFIG
# =============================

SERVER_API = "https://frxchat.alwaysdata.net/api/bot/bot_messages.php"
SEND_API   = "https://frxchat.alwaysdata.net/api/bot/send_bot_message.php"

BOT_USER_ID = 14
CONV_WITH_ID = 17
SLEEP_SECONDS = 2

QUIZ_STATE_FILE  = "quiz_state.json"
QUIZ_SCORES_FILE = "quiz_scores.json"
MONEY_FILE       = "money.json"
INVENTORY_FILE   = "inventory.json"
VIP_FILE         = "vip.json"
LAST_ID_FILE     = "last_id.txt"

print("✅ Bot Python démarré...")

# =============================
# UTILITAIRES FICHIERS
# =============================

def load_json(file):
    if not os.path.exists(file):
        return {}
    with open(file, "r") as f:
        return json.load(f)

def save_json(file, data):
    with open(file, "w") as f:
        json.dump(data, f)

# =============================
# FONCTIONS BOT
# =============================

def send_message(content):
    try:
        requests.post(SEND_API, data={
            "bot_user_id": BOT_USER_ID,
            "conversation_with_id": CONV_WITH_ID,
            "content": content
        })
    except Exception:
        pass

# === Quiz ===
def get_random_quiz_question():
    questions = [
        {"q": "Quelle est la capitale de la France ?", "a": "paris"},
        {"q": "Combien font 5 + 7 ?", "a": "12"},
        {"q": "Qui a peint la Joconde ?", "a": "leonard de vinci"},
        {"q": "Quelle planète est la plus proche du Soleil ?", "a": "mercure"},
    ]
    return random.choice(questions)

def add_point(user):
    data = load_json(QUIZ_SCORES_FILE)
    data[str(user)] = data.get(str(user), 0) + 1
    save_json(QUIZ_SCORES_FILE, data)
    return data[str(user)]

def get_quiz_ranking():
    data = load_json(QUIZ_SCORES_FILE)
    if not data:
        return "Aucun point."
    sorted_scores = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = "🏆 Classement Quiz :\n"
    for i, (user, pts) in enumerate(sorted_scores[:10], 1):
        msg += f"{i}. {user} — {pts} pts\n"
    return msg.strip()

# === Monnaie ===
def add_money(user, amount):
    data = load_json(MONEY_FILE)
    data[str(user)] = data.get(str(user), 0) + amount
    save_json(MONEY_FILE, data)
    return data[str(user)]

def get_wallet(user):
    data = load_json(MONEY_FILE)
    return data.get(str(user), 0)

def get_money_ranking():
    data = load_json(MONEY_FILE)
    if not data:
        return "Aucune donnée."
    sorted_data = sorted(data.items(), key=lambda x: x[1], reverse=True)
    msg = "🏦 Top Fortune :\n"
    for i, (user, amt) in enumerate(sorted_data[:10], 1):
        msg += f"{i}. {user} — {amt} 💰\n"
    return msg.strip()

# === Boutique / Inventaire ===
SHOP_ITEMS = {
    1: {"name": "VIP", "price": 10},
    2: {"name": "Titre Débutant", "price": 10},
    3: {"name": "Titre Intermédiaire", "price": 50},
    4: {"name": "Titre Confirmé", "price": 100},
    5: {"name": "Titre Pro", "price": 200},
}

def add_item_to_inventory(user, item_id):
    inv = load_json(INVENTORY_FILE)
    inv.setdefault(str(user), []).append(item_id)
    save_json(INVENTORY_FILE, inv)

def get_user_inventory(user):
    inv = load_json(INVENTORY_FILE)
    return inv.get(str(user), [])

def show_shop():
    msg = "🛒 Boutique :\n"
    for id, item in SHOP_ITEMS.items():
        msg += f"{id}. {item['name']} — {item['price']} 💰\n"
    msg += "\nUtilise : ?buy ID"
    return msg.strip()

def show_inventory(user):
    inv = get_user_inventory(user)
    if not inv:
        return "📦 Inventaire vide."
    msg = f"🎒 Inventaire:\n"
    for i, item_id in enumerate(inv, 1):
        name = SHOP_ITEMS.get(item_id, {}).get("name", f"Item {item_id}")
        msg += f"{i}. {name}\n"
    msg += "\nUtilise : ?use ID"
    return msg.strip()

def buy_item(user, item_id):
    if item_id not in SHOP_ITEMS:
        return "❌ Item invalide."
    price = SHOP_ITEMS[item_id]["price"]
    balance = get_wallet(user)
    if balance < price:
        return "❌ Pas assez d'argent."
    add_money(user, -price)
    add_item_to_inventory(user, item_id)
    return f"✅ Achat réussi : {SHOP_ITEMS[item_id]['name']} — Solde restant: {get_wallet(user)} 💰"

def use_item(user, item_id):
    inv = get_user_inventory(user)
    if item_id not in inv:
        return "❌ Tu ne possèdes pas cet item."
    inv.remove(item_id)
    all_inv = load_json(INVENTORY_FILE)
    all_inv[str(user)] = inv
    save_json(INVENTORY_FILE, all_inv)

    # Effets des items
    if item_id == 1:  # VIP
        vip = load_json(VIP_FILE)
        vip[str(user)] = {"remaining": 3}  # 3 quiz bonus
        save_json(VIP_FILE, vip)
        return "👑 VIP activé ! +30 pièces sur tes 3 prochains quiz gagnés."
    else:
        return f"✅ Item {SHOP_ITEMS[item_id]['name']} utilisé."

# =============================
# LAST ID
# =============================

last_id = 0
if os.path.exists(LAST_ID_FILE):
    with open(LAST_ID_FILE, "r") as f:
        last_id = int(f.read() or 0)

# =============================
# BOUCLE PRINCIPALE
# =============================

while True:

    try:
        r = requests.get(SERVER_API, params={
            "bot_user_id": BOT_USER_ID,
            "conversation_with_id": CONV_WITH_ID
        })
        messages = r.json()
    except Exception:
        time.sleep(SLEEP_SECONDS)
        continue

    if not isinstance(messages, list):
        time.sleep(SLEEP_SECONDS)
        continue

    for msg in messages:

        if msg["id"] <= last_id:
            continue
        if msg["sender_id"] == BOT_USER_ID:
            continue

        user = msg["sender_id"]
        text = msg["content"].strip().lower()
        response = None

        # =============================
        # COMMANDES
        # =============================
        if text == "?help":
            response = "?help\n?quiz\n?classementquiz\n?wallet\n?classementwallet\n?shop\n?inventory\n?buy ID\n?use ID\n?meteo\n?pop"
        elif text == "?quiz":
            quiz = load_json(QUIZ_STATE_FILE)
            if quiz.get("active"):
                response = "⏳ Quiz déjà actif."
            else:
                question = get_random_quiz_question()
                save_json(QUIZ_STATE_FILE, {
                    "question": question["q"],
                    "answer": question["a"].lower(),
                    "active": True,
                    "start_time": time.time(),
                    "duration": 30
                })
                response = f"🎯 QUIZ (30s) : {question['q']}"
        elif text == "?classementquiz":
            response = get_quiz_ranking()
        elif text == "?wallet":
            balance = get_wallet(user)
            response = f"💰 Tu as {balance} pièces."
        elif text == "?shop":
            response = show_shop()
        elif text == "?inventory":
            response = show_inventory(user)
        elif text.startswith("?buy "):
            try:
                item_id = int(text.split()[1])
                response = buy_item(user, item_id)
            except (ValueError, IndexError):
                response = "❌ Syntaxe : ?buy ID"
        elif text.startswith("?use "):
            try:
                item_id = int(text.split()[1])
                response = use_item(user, item_id)
            except (ValueError, IndexError):
                response = "❌ Syntaxe : ?use ID"
        elif text == "?meteo":
            try:
                response = requests.get("https://wttr.in/Nancy?format=3").text
            except Exception:
                response = "Erreur météo"
        elif text == "?classementwallet":
            response = get_money_ranking()
        elif text == "?pop":
            try:
                r = requests.get("https://api.worldbank.org/v2/country/WLD/indicator/SP.POP.TOTL",
                                 params={"format": "json", "per_page": 1})
                data = r.json()
                response = str(data[1][0]["value"])
            except Exception:
                response = "Erreur API"

        # =============================
        # GESTION QUIZ
        # =============================
        quiz = load_json(QUIZ_STATE_FILE)
        vip_data = load_json(VIP_FILE)

        if quiz.get("active") and response is None:
            if time.time() - quiz["start_time"] >= quiz["duration"]:
                response = f"⏰ Temps écoulé ! Réponse : {quiz['answer']}"
                save_json(QUIZ_STATE_FILE, {"active": False})
                # VIP annulé si temps écoulé
                if str(user) in vip_data:
                    del vip_data[str(user)]
                    save_json(VIP_FILE, vip_data)
                    send_message("❌ Série VIP interrompue, bonus annulé.")

            elif text == quiz["answer"]:
                points_to_add = 1
                money_to_add = 10

                # VIP
                if str(user) in vip_data:
                    money_to_add += 30
                    vip_data[str(user)]["remaining"] -= 1
                    if vip_data[str(user)]["remaining"] <= 0:
                        del vip_data[str(user)]
                        send_message("👑 VIP terminé ! Tes 3 bonus ont été utilisés.")
                    save_json(VIP_FILE, vip_data)

                score = add_point(user)
                money = add_money(user, money_to_add)
                response = f"✅ Bonne réponse !\n⭐ {score} pts\n💰 +{money_to_add} (Total: {money})"
                save_json(QUIZ_STATE_FILE, {"active": False})

        # =============================
        # ENVOI REPONSE
        # =============================
        if response:
            send_message(response)

        last_id = msg["id"]
        with open(LAST_ID_FILE, "w") as f:
            f.write(str(last_id))

    time.sleep(SLEEP_SECONDS)
