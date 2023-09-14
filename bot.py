import logging
import time
import requests
from bs4 import BeautifulSoup
import threading
from telegram import __version__ as TG_VER,Bot
import json
import asyncio
import credentials
import lista_libri

_path = "/root/scraper_libraccio/lista_libri.json" 
_path = "/home/chris/Documents/scraper_libraccio/lista_libri.json"


try:

    from telegram import __version_info__

except ImportError:

    __version_info__ = (0, 0, 0, 0, 0)  # type: ignore[assignment]


if __version_info__ < (20, 0, 0, "alpha", 1):

    raise RuntimeError(

        f"This example is not compatible with your current PTB version {TG_VER}. To view the "

        f"{TG_VER} version of this example, "

        f"visit https://docs.python-telegram-bot.org/en/v{TG_VER}/examples.html"

    )

from telegram import ForceReply, Update

from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters


# Enable logging

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)

# set higher logging level for httpx to avoid all GET and POST requests being logged

logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)



# Define a few command handlers. These usually take the two arguments update and

# context.

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /start is issued."""

    user = update.effective_user

    await update.message.reply_html(

        rf"Ciao {user.mention_html()}! Benvenuto sul bot non ufficiale di libraccio.it"
    )
    await update.message.reply_text("Questo bot è stato progettato per avvisarti non appena un libro che stai cercando appare usato su libraccio, in modo da essere il primo/a a vederlo.")
    await update.message.reply_text("Per iniziare a monitorare un libro inserisci il comando /ricerca per poi inserire nel messaggio successivo il link libraccio del libro in questione.")

check_inserito = 0
async def ricerca(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global check_inserito
    check_inserito = 1
    await update.message.reply_text("Inserisci il link del libro")

async def scraping() -> None:
    def monitora(link):
        url = requests.get(link)
        bs = BeautifulSoup(url.content,"html.parser")
        stato = bs.find("div",class_="buybox-used")
        return stato != None,link ##ritorna True se il libro c'è usato, False se non c'è usato
    bot= Bot(token=credentials.token)
    while True:
        for id,lista in lista_libri.file.items():
            for idx,libro in enumerate(lista):
                q = monitora(libro)
                #print(libro)
                if q[0]:
                    await bot.sendMessage(id,f"E' stato trovato un libro usato al seguente link: {q[1]}")
                    del lista_libri.file[id][idx]

        
        await asyncio.sleep(1)
def _scraping():
    asyncio.run(scraping())
async def miei_libri(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        
        userid = str(update.message.from_user["id"])
        s = ""
        for x in lista_libri.file[userid]:
            s+=x + "\n\n"

        s = s[:-1]
        await update.message.reply_text("Ecco i libri che hai inserito nel database: \n" + s)
 

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /help is issued."""

    await update.message.reply_text("Help!")
    

async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    global check_inserito

    flag = 1
    userid = str(update.message.from_user["id"])

    if check_inserito:
        check_inserito = 0

        try: 
            r = requests.get(update.message.text)
            if r.status_code != 200:
                raise Exception
        except:
            await update.message.reply_text("Il link inserito non è valido, per favore controlla se hai inserito il link di un libro presente su libraccio.it e reinvialo")
            check_inserito = 1
            flag = 0
            return
        await update.message.reply_text("Il libro è stato salvato nel database, verrai avvisato non appena sarà disponibile usato")
        #! w+ non si può usare perché il contenuto del file prima viene azzerato e poi viene letto, per cui

        with open(_path,"w") as file:
            if lista_libri.file.get(userid) == None:
                lista_libri.file[userid] = []
            lista_libri.file[userid].append(update.message.text)

            print(f"Aggiunto {update.message.text}")
def main() -> None:

    """Start the bot."""

    # Create the Application and pass it your bot's token.

    application = Application.builder().token(credentials.token).build()

    # on different commands - answer in Telegram

    application.add_handler(CommandHandler("start", start))

    application.add_handler(CommandHandler("start", start))
    
    application.add_handler(CommandHandler("libri", miei_libri))

    application.add_handler(CommandHandler("ricerca", ricerca))

    application.add_handler(CommandHandler("help", help_command))


    # on non command i.e message - echo the message on Telegram

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))


    # Run the bot until the user presses Ctrl-C

    application.run_polling(allowed_updates=Update.ALL_TYPES)



def _start(): 
    t1 = threading.Thread(target=_scraping,group=None)
    t1.start()
    main()

_start()

