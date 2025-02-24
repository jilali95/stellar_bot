import os
import time
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext
import pandas as pd

users_s = os.getenv("USERS_S")  # Read from environment variables

# Convert it into a list of integers
if users_s:
    ALLOWED_USERS = [int(x) for x in users_s.split(',')]
else:
    ALLOWED_USERS = []
# Get the Google Drive link from GitHub Secrets
google_drive_link = os.getenv("CSV_DATA", "").strip()

if google_drive_link:
    try:
        output = "stock.csv"  # Name of the downloaded file

        # Download the file using gdown with the full link
        gdown.download(google_drive_link, output, quiet=False)

        # Read the CSV file
        df = pd.read_csv(output)
        print(df.head())  # Debugging (remove later)

    except Exception as e:
        print(f"⚠️ Error downloading CSV: {e}")

else:
    print("⚠️ Error: CSV_DATA secret not found or empty!")

else:
    print("⚠️ Error: csv_data secret not found!")
last_modification = pd.Timestamp(pd.to_datetime(time.ctime(os.path.getmtime('stock.csv')))).strftime('%d.%m.%y')
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

async def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    print(user_id, " _ ", user_name)

    if user_id in ALLOWED_USERS:
        user_input = update.message.text.strip().lower()
        search_term = user_input

        matches = []

        for _, row in df.iterrows():
            if all(word in str(row['ARTICLE']).lower() for word in search_term.split()):
                benif = ((row['pharmacien'] - row['DERNIER_PRIX_ACHAT'])/row['DERNIER_PRIX_ACHAT']) * 100
                matches.append(f"{row['ARTICLE']},\ngrossiste: {row['DERNIER_PRIX_ACHAT']:.2f} DA,\nPharmacien: {row['pharmacien']:.2f} DA,\nbenif: {benif:.0f} %\nQNT: {row['QTE']}")

        if matches:
            await update.message.reply_text(f"\n________________________________\n".join(matches))
            num_articles = len(matches)
            await update.message.reply_text(f"\nNumber of articles: {num_articles}\n{last_modification}")
        else:
            await update.message.reply_text("No exact matches found. Please refine your search.")

    else:
        await update.message.reply_text("You are not authorized to use this bot.")

def main():
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))
    application.add_handler(CommandHandler('h', h))
    application.run_polling()

if __name__ == '__main__':
    main()

