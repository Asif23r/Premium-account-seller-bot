from pyrogram import Client, filters
import json, os

BOT_TOKEN = "YOUR_BOT_TOKEN"  # Replace this with your BotFather token
OWNER_ID = 123456789          # Replace this with your Telegram ID

if not os.path.exists("db.json"):
    with open("db.json", "w") as f:
        json.dump({"users": {}, "admins": [OWNER_ID], "requests": {}}, f, indent=4)

app = Client("refer_bot", bot_token=BOT_TOKEN)

def load_db():
    with open("db.json") as f:
        return json.load(f)

def save_db(data):
    with open("db.json", "w") as f:
        json.dump(data, f, indent=4)

def is_admin(uid):
    db = load_db()
    return int(uid) in db["admins"]

@app.on_message(filters.command("start"))
def start(client, message):
    db = load_db()
    uid = str(message.from_user.id)
    name = message.from_user.first_name

    if uid not in db["users"]:
        db["users"][uid] = {"points": 0, "ref_by": None}
        save_db(db)

    message.reply(
        f"👋 Hello {name}!\n\n"
        "🎯 Earn points by referring your friends!\n"
        "➕ Use `/refer <user_id>` to get 0.4 point.\n"
        "💰 When you reach 1 point, use `/buy` to request an account.\n"
        "💼 Check points: `/points`"
    )

@app.on_message(filters.command("refer"))
def refer(client, message):
    db = load_db()
    uid = str(message.from_user.id)

    if uid not in db["users"]:
        return message.reply("❌ Type /start first.")

    if db["users"][uid]["ref_by"]:
        return message.reply("⚠️ You've already used a referral.")

    if len(message.command) < 2:
        return message.reply("❗Usage: `/refer <user_id>`")

    ref_id = message.command[1]

    if ref_id == uid:
        return message.reply("❌ You cannot refer yourself!")

    if ref_id not in db["users"]:
        return message.reply("🚫 Invalid referral ID!")

    db["users"][uid]["ref_by"] = ref_id
    db["users"][ref_id]["points"] += 0.4
    save_db(db)

    message.reply("✅ Referral successful! 0.4 point added to your friend.")

@app.on_message(filters.command("points"))
def points(client, message):
    db = load_db()
    uid = str(message.from_user.id)

    if uid not in db["users"]:
        return message.reply("❌ Type /start first.")

    pts = db["users"][uid]["points"]
    message.reply(f"💸 You have {pts:.1f} point(s).")

@app.on_message(filters.command("buy"))
def buy(client, message):
    db = load_db()
    uid = str(message.from_user.id)

    if uid not in db["users"]:
        return message.reply("❌ Type /start first.")

    if db["users"][uid]["points"] < 1:
        return message.reply("⚠️ You need at least 1 point to buy!\nRefer more friends.")

    if uid in db["requests"]:
        return message.reply("🕐 Your request is already pending.")

    db["requests"][uid] = "pending"
    save_db(db)

    message.reply("🛍️ Buy request sent to admin. Please wait for verification.")

    for admin in db["admins"]:
        try:
            client.send_message(admin, f"🔔 Buy request from `{uid}`.\nVerify using: `/verify {uid}`")
        except:
            pass

@app.on_message(filters.command("verify") & filters.user(OWNER_ID))
def verify(client, message):
    db = load_db()
    if len(message.command) < 2:
        return message.reply("❗Usage: /verify <user_id>")

    uid = message.command[1]

    if uid not in db["requests"]:
        return message.reply("❌ No such pending request.")

    db["users"][uid]["points"] -= 1
    del db["requests"][uid]
    save_db(db)

    client.send_message(int(uid), "✅ Your account is ready! Admin has approved your request.")
    message.reply(f"✅ {uid} verified and 1 point deducted.")

@app.on_message(filters.command("addadmin") & filters.user(OWNER_ID))
def addadmin(client, message):
    db = load_db()
    if len(message.command) < 2:
        return message.reply("Usage: /addadmin <user_id>")
    new_admin = int(message.command[1])
    if new_admin not in db["admins"]:
        db["admins"].append(new_admin)
        save_db(db)
        message.reply(f"✅ {new_admin} added as admin.")
    else:
        message.reply("Already admin.")

@app.on_message(filters.command("removeadmin") & filters.user(OWNER_ID))
def removeadmin(client, message):
    db = load_db()
    if len(message.command) < 2:
        return message.reply("Usage: /removeadmin <user_id>")
    uid = int(message.command[1])
    if uid in db["admins"]:
        db["admins"].remove(uid)
        save_db(db)
        message.reply(f"✅ {uid} removed from admin list.")
    else:
        message.reply("❌ Not an admin.")

app.run()