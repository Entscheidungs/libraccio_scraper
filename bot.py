import logging,credentials,requests,threading,json,asyncio
from bs4 import BeautifulSoup 


from telegram import __version__ as TG_VER,Bot

from telegram import ForceReply, Update

from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler



path = "/home/chris/Documents/Programmazione/Python/libraccio/lista.json"
#path = "/root/scraper_libraccio/lista.json"

# Enable logging

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)

# set higher logging level for httpx to avoid all GET and POST requests being logged

logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)



# Define a few command handlers. These usually take the two arguments update and

# context.

INSERT,SCRAPE, REQ, LIST = range(4)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /start is issued."""


    await update.message.reply_text("Questo bot ti è utile nel caso tu voglia comprare un libro su libraccio.it usato, ma sul sito sia presente solamente nuovo.")
    await update.message.reply_text("Inserendo il comando /ricerca ed inviando poi il link del libro in questione (attenzione, il link deve essere di un libro, non di un autore o altro), lo stato del libro verrà monitorato periodicamente dal bot, che ti avviserà quando sarà disponibile usato.")
    await update.message.reply_text("Infine puoi visualizzare la lista dei libri che il bot sta monitorando tramite il comando /miei_libri.")
    await update.message.reply_text("Questo bot è in fase di testing, il creatore si scusa per eventuali malfunzionamenti, per qualsiasi chiarimento siete pregati di contattare @zzeroxchris")
    await update.message.reply_text("Il codice sorgente del bot è inoltre disponibile su github al link https://github.com/Entscheidungs/libraccio_scraper e se ti è tornato utile sei pregato di lasciare una star!")


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /help is issued."""

    await update.message.reply_text("Help!")



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Echo the user message."""

    await update.message.reply_text(update.message.text)



async def inserting_book(update: Update, context: ContextTypes.DEFAULT_TYPE): # it asks to enter the link of the book
    await update.message.reply_text("Inserisci il link del libro che vorresti trovare usato\n") #asks for the link to the book 
    return INSERT

async def inserting(update: Update, context: ContextTypes.DEFAULT_TYPE): # it asks to enter the link of the book 
    link = update.message.text
    try:
        x = requests.get(link).text
        if "Errore generico" in x:
            raise Exception
        link = update.message.text
    except:
        await update.message.reply_text("Il link inserito non risulta valido, sicuro che sia il link completo di un libro?")
        await update.message.reply_text("Inserisci il link del libro che vorresti trovare usato\n") 
        return INSERT

  
    obj.acquire()
    with open(path,"r") as f: #the content of the json file is temporaily stored in a dictionary
        jsondict = json.load(f)
    userid = str(update.message.from_user["id"])

    if not jsondict.get(userid): #if the user didn't insert any book, the user id is store in the json file
        jsondict[userid] = []

    #if the book is already saved, the user is informed
    #await update.message.reply_text("Libro già presente nel database") if link in jsondict[userid] else (jsondict[userid].append(link),await update.message.reply_text("il libro è stato inserito nel database"))
    
    #if the book is already saved, the user is informed
    if link in jsondict[userid]: 
        await update.message.reply_text("Questo libro è già presente nel database")
    else:
        jsondict[userid].append(link)
        with open(path,"w") as f: #the json file is updated
            json.dump(jsondict,f)
        await update.message.reply_text("Il libro è stato inserito nel database")
    
    obj.release()
    return ConversationHandler.END
def _scraping():
    asyncio.run(scraping())
    
    
    
async def scraping(): #this function scrapes the webpage of libraccio.it searching for the buybox-used div class
    bot= Bot(token=credentials.token)
    while True:
        obj.acquire()
        with open(path,"r") as f:
            jsondict = json.load(f)
        
        newdict = {} #the new dict will contain only the books who are not found 
        for userid in jsondict.keys():
            newdict[userid] = []
            for book in jsondict[userid]:
                url = requests.get(book)
                bs = BeautifulSoup(url.content,"html.parser")
                success = bs.find("div",class_="buybox-used")
                if success:
                    try:
                        await bot.send_message(text=f"Buone notizie, un libro che stavi cercando è stato trovato usato:\n{book}",chat_id=userid)
                    except:
                        pass
                else:
                    newdict[userid].append(book)
        with open(path,"w") as f:
            json.dump(newdict,f)

        obj.release()
        await asyncio.sleep(5)



async def show_list(update: Update, context: ContextTypes.DEFAULT_TYPE): # it asks to enter the link of the book
    userid = str(update.message.from_user["id"])
    with open(path,"r") as f:
        jsondict = json.load(f)
    
    msg = ""
    if jsondict.get(userid):
        for x in jsondict[userid]:
            msg+=x
            msg+="\n\n"
        await update.message.reply_text(f"Ecco i libri che stai cercando {msg}")
    else:
        await update.message.reply_text(f"Non hai inserito nessun libro")
        
    return ConversationHandler.END
def main() -> None:

    """Start the bot."""

    # Create the Application and pass it your bot's token.

    application = Application.builder().token(credentials.token).build()


    # on different commands - answer in Telegram

    conv_handler = ConversationHandler(entry_points=[CommandHandler("start",start),CommandHandler("ricerca",inserting_book),CommandHandler("lista_libri",show_list),CommandHandler("miei_libri",show_list)],
    states = {INSERT : [MessageHandler(filters.TEXT, inserting)], REQ : [CommandHandler("ricerca",inserting_book)]},fallbacks=[],)


    


    application.add_handler(conv_handler)


    # Run the bot until the user presses Ctrl-C

    application.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == "__main__":


    obj = threading.Semaphore(1)
    _thread = threading.Thread(target=_scraping)
    _thread.start()
    while True:
        try: main()
        except: main()
