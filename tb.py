import io
import urllib.request
import os , time, logging
import os , time, logging
import pandas as pd
from telegram import Update
from telegram.ext import Application, MessageHandler, filters, CallbackContext


users_s = os.getenv("USERS_S", "").strip()
ALLOWED_USERS = [int(x) for x in users_s.split(',')] if users_s else []
def load_stock_data():
    file_id = os.getenv("CSV_URL")
    print(file_id)
    # Set display options to show all rows and all columns
    pd.set_option('display.max_rows', None)

    url = f"https://drive.google.com/uc?id={file_id}&export=download"

    # Fetch the CSV data
    with urllib.request.urlopen(url) as response:
        data = response.read()

    # Decode the data using ISO-8859-1 encoding
    text_data = data.decode('ISO-8859-1')

    # Create an in-memory file object
    csv_file = io.StringIO(text_data)
    try:
        df = pd.read_csv(csv_file, delimiter=';', encoding='ISO-8859-1')
        last_modification = time.strftime('%d.%m.%y', time.localtime(os.path.getmtime('stock.csv')))
        return df, last_modification
    except Exception as e:
        logging.error(f"Error loading stock.csv: {e}")
        return pd.DataFrame(), "N/A" 

async def handle_text(update: Update, context: CallbackContext):
    user_id = update.message.from_user.id
    user_name = update.message.from_user.first_name
    logging.info(f"User {user_name} ({user_id}) sent a message.")

    if user_id in ALLOWED_USERS:
        user_input = update.message.text.strip().lower()
        df, last_modification = load_stock_data()

        if df.empty:
            await update.message.reply_text("Error: Unable to load stock data. Please try again later.")
            return

        # Optimized search using Pandas
        filtered_df = df[df['ARTICLE'].str.lower().str.contains(user_input, na=False)]

        if not filtered_df.empty:
            results = [
                f"{row['ARTICLE']},\n"
                f"Grossiste: {row['DERNIER_PRIX_ACHAT']:.2f} DA,\n"
                f"Pharmacien: {row['pharmacien']:.2f} DA,\n"
                f"Bénéfice: {((row['pharmacien'] - row['DERNIER_PRIX_ACHAT']) / row['DERNIER_PRIX_ACHAT']) * 100:.0f} %\n"
                f"QNT: {row['QTE']}"
                for _, row in filtered_df.iterrows()
            ]

            message_text = "\n________________________________\n".join(results)
            await update.message.reply_text(message_text)
            await update.message.reply_text(f"\nNombre d'articles: {len(filtered_df)}\nDernière mise à jour: {last_modification}")
        else:
            await update.message.reply_text("Aucun article trouvé. Veuillez affiner votre recherche.")

    else:
        await update.message.reply_text("Vous n'êtes pas autorisé à utiliser ce bot.")

# ✅ Main function to start the bot
def main():
    print(os.getenv("TELEGRAM_BOT_TOKEN"))
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).build()
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    application.run_polling()

if __name__ == '__main__':
    main()
