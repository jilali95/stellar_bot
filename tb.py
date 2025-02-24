import os
import time
import pandas as pd
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

# ✅ Read allowed users from GitHub Secret
users_s = os.getenv("USERS_S", "").strip()
ALLOWED_USERS = [int(x) for x in users_s.split(',')] if users_s else []

# ✅ Get the Google Drive link from GitHub Secrets
google_drive_link = os.getenv("CSV_DATA", "").strip()

df = None  # Initialize to avoid errors if CSV fails to load
last_modification = "Unknown"  # Default in case we can't get the date

if google_drive_link:
    try:
        # ✅ Get last modification date from Google Drive HTTP headers
        response = requests.head(google_drive_link)
        if "Last-Modified" in response.headers:
            last_modification = time.strftime('%d.%m.%y', time.strptime(response.headers["Last-Modified"], "%a, %d %b %Y %H:%M:%S %Z"))

        # ✅ Read CSV directly from the Google Drive link
        df = pd.read_csv(google_drive_link)

    except Exception as e:
        print(f"⚠️ Error reading CSV: {e}")
else:
    print("⚠️ Error: CSV_DATA secret not found!")

# ✅ Handle "/h" command
async def h(update: Update, context: CallbackContext):
    bot = context.bot
    commands = [
        ('a', 'Start the bot'),
        ('v', 'Get help information'),
        ('h', 'Show bot information'),
        ('z', 'Show bot information')
    ]
    await bot.set_my_commands(commands)
    await update.message.reply_text("Menu button updated with commands.")

# ✅ Handle text messages
async def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    print(user_id, " _ ", user_name)

    if user_id in ALLOWED_USERS:
        if df is None:
            await update.message.reply_text("⚠️ Data not available. Please check the CSV source.")
            return

        user_input = update.message.text.strip().lower()
        search_term = user_input
        matches = []

        for _, row in df.iterrows():
            if all(word in str(row['ARTICLE']).lower() for word in search_term.split()):
                benif = ((row['pharmacien'] - row['DERNIER_PRIX_ACHAT']) / row['DERNIER_PRIX_ACHAT']) * 100
                matches.append(f"{row['ARTICLE']},\ngrossiste: {row['DERNIER_PRIX_ACHAT']:.2f} DA,\n"
                               f"Pharmacien: {row['pharmacien']:.2f} DA,\nbenif: {benif:.0f} %\nQNT: {row['QTE']}")

        if matches:
            await update.message.reply_text(f"\n________________________________\n".join(matches))
            num_articles = len(matches)
            await update.message.reply_text(f"\nNumber of articles: {num_articles}\nLast Update: {last_modification}")
        else:
            await update.message.reply_text("No exact matches found. Please refine your search.")
    else:
        await update.message.reply_text("You are not authorized to use this bot.")

# ✅ Main function to start the bot
def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CommandHandler('h', h))
    application.run_polling()

if __name__ == '__main__':
    main()
