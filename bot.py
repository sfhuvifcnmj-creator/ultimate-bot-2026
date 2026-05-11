cat <<EOF > bot.py
import telebot
from telebot import types
from sqlitedict import SqliteDict
import time

API_TOKEN = '8784900019:AAFAcPdTs4axum_RyjvZ-NMfqW7jbKCiR_g'
ADMIN_ID = 6363022206 
bot = telebot.TeleBot(API_TOKEN)
db = SqliteDict('./global_earn_data.sqlite', autocommit=True)

# Initial Setup
if 'settings' not in db:
    db['settings'] = {
        'msg_welcome': "Welcome to the system.",
        'btn_ads': "View Ads",
        'btn_offers': "Offers Wall",
        'btn_tasks': "Tasks",
        'btn_profile': "Profile",
        'btn_withdraw': "Withdraw",
        'ad_link': "https://google.com",
        'ad_price': 0.01,
        'min_withdraw': 5.0,
        'fee': 0.04
    }
if 'tasks' not in db: db['tasks'] = []

def get_menu():
    s = db['settings']
    m = types.InlineKeyboardMarkup(row_width=2)
    m.add(
        types.InlineKeyboardButton(s['btn_ads'], callback_data="ads"),
        types.InlineKeyboardButton(s['btn_offers'], callback_data="offers"),
        types.InlineKeyboardButton(s['btn_tasks'], callback_data="tasks"),
        types.InlineKeyboardButton(s['btn_profile'], callback_data="profile"),
        types.InlineKeyboardButton(s['btn_withdraw'], callback_data="withdraw")
    )
    return m

@bot.message_handler(commands=['start'])
def start(m):
    uid = str(m.chat.id)
    if uid not in db: db[uid] = {'balance': 0.0}
    bot.send_message(m.chat.id, db['settings']['msg_welcome'], reply_markup=get_menu())

@bot.message_handler(func=lambda m: m.chat.id == ADMIN_ID)
def admin(m):
    s = db['settings']
    t = m.text
    if t.startswith("set_msg "):
        s['msg_welcome'] = t.replace("set_msg ", "")
        db['settings'] = s
        bot.reply_to(m, "Welcome message updated.")
    elif t.startswith("set_btn_ads "):
        s['btn_ads'] = t.replace("set_btn_ads ", "")
        db['settings'] = s
        bot.reply_to(m, "Ads button text updated.")
    elif t.startswith("set_link "):
        s['ad_link'] = t.replace("set_link ", "").strip()
        db['settings'] = s
        bot.reply_to(m, "Offers link updated.")
    elif t.startswith("set_fee "):
        s['fee'] = float(t.replace("set_fee ", "").strip())
        db['settings'] = s
        bot.reply_to(m, f"Fee set to {s['fee']}")
    elif t.startswith("add_task "):
        parts = t.replace("add_task ", "").split("|")
        all_t = db['tasks']
        all_t.append({'n': parts[0].strip(), 'l': parts[1].strip(), 'p': float(parts[2].strip())})
        db['tasks'] = all_t
        bot.reply_to(m, "Task added.")
    elif t == "clear_tasks":
        db['tasks'] = []
        bot.reply_to(m, "All tasks deleted.")

@bot.callback_query_handler(func=lambda c: True)
def calls(c):
    uid = str(c.message.chat.id)
    s = db['settings']
    if c.data == "ads":
        time.sleep(2)
        u = db[uid]
        u['balance'] += s['ad_price']
        db[uid] = u
        bot.send_message(c.message.chat.id, f"Added {s['ad_price']}", reply_markup=get_menu())
    elif c.data == "offers":
        m = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton("Open", url=s['ad_link']))
        bot.send_message(c.message.chat.id, "Available Offers:", reply_markup=m)
    elif c.data == "profile":
        bot.send_message(c.message.chat.id, f"Balance: {db[uid]['balance']:.3f}$")
    elif c.data == "tasks":
        tk = db['tasks']
        if not tk: return
        m = types.InlineKeyboardMarkup()
        for i in tk: m.add(types.InlineKeyboardButton(f"{i['n']} - {i['p']}$", url=i['l']))
        bot.send_message(c.message.chat.id, "Tasks:", reply_markup=m)
    elif c.data == "withdraw":
        u = db[uid]
        if u['balance'] >= s['min_withdraw']:
            net = u['balance'] - s['fee']
            msg = bot.send_message(c.message.chat.id, f"Net: {net}$ - Send Wallet:")
            bot.register_next_step_handler(msg, lambda m: bot.send_message(ADMIN_ID, f"Withdraw Request:\nNet: {net}\nWallet: {m.text}"))
        else:
            bot.answer_callback_query(c.id, f"Min: {s['min_withdraw']}$", show_alert=True)

print("System Active - Full Control Enabled")
bot.infinity_polling()
EOF
python3 bot.py
