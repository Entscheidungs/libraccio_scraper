import logging,credentials,requests,threading,json,asyncio
from bs4 import BeautifulSoup 


from telegram import __version__ as TG_VER,Bot

from telegram import ForceReply, Update

from telegram.ext import Application, CommandHandler, ContextTypes, MessageHandler, filters, ConversationHandler



path = "/home/chris/Documents/Programmazione/Python/libraccio/lista.json"

# Enable logging

logging.basicConfig(

    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO

)

# set higher logging level for httpx to avoid all GET and POST requests being logged

logging.getLogger("httpx").setLevel(logging.WARNING)


logger = logging.getLogger(__name__)



# Define a few command handlers. These usually take the two arguments update and

# context.

INSERT,SCRAPE = range(2)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /start is issued."""

    user = update.effective_user

    await update.message.reply_html(

        rf"Hi {user.mention_html()}!",

        reply_markup=ForceReply(selective=True),

    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Send a message when the command /help is issued."""

    await update.message.reply_text("Help!")



async def echo(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:

    """Echo the user message."""

    await update.message.reply_text(update.message.text)



async def req(update: Update, context: ContextTypes.DEFAULT_TYPE): # it asks to enter the link of the book
    await update.message.reply_text("Inserisci il link del libro che vorresti trovare usato\n") #asks for the link to the book 
    return INSERT

def _scraping():
    asyncio.run(scraping())
async def scraping(): #this function scrapes the webpage of libraccio.it searching for the buybox-used div class

    bot= Bot(token=credentials.token)
    while True:
       
        with open(path,"r") as f:
            jsondict = json.load(f)
        
        newdict = {} #the new dict will contain only the books who are not found 
        for list_of_books in jsondict.keys():
            newdict[list_of_books] = []
            for book in jsondict[list_of_books]:
                url = requests.get(book)
                bs = BeautifulSoup(url.content,"html.parser")
                stato = bs.find("div",class_="buybox-used")
                if stato:
                   await bot.send_message(text=f"Buone notizie, un libro che stavi cercando è stato trovato usato:\n{book}",chat_id=list_of_books)
                else:
                    newdict[list_of_books].append(book)
        
        with open(path,"w") as f:
            json.dump(newdict,f)
    
        await asyncio.sleep(5)
async def inserting(update: Update, context: ContextTypes.DEFAULT_TYPE): # it asks to enter the link of the book
    link = update.message.text


    with open(path,"r") as f: #the content of the json file is temporaily stored in a dictionary
        jsondict = json.load(f)
    userid = str(update.message.from_user["id"])

    if not jsondict.get(userid): #if the user didn't insert any book, the user id is store in the json file
        jsondict[userid] = []

    #if the book is already saved, the user is informed
    await update.message.reply_text("Libro già presente nel database") if link in jsondict[userid] else jsondict[userid].append(link)

    with open(path,"w") as f: #the json file is updated
        json.dump(jsondict,f)

    return ConversationHandler.END


    
def main() -> None:

    """Start the bot."""

    # Create the Application and pass it your bot's token.

    application = Application.builder().token(credentials.token).build()


    # on different commands - answer in Telegram

    conv_handler = ConversationHandler(entry_points=[CommandHandler("start",start),CommandHandler("ricerca",req)],
    states = {INSERT : [MessageHandler(filters.TEXT, inserting)]},fallbacks=[],)
    


    application.add_handler(conv_handler)


    # Run the bot until the user presses Ctrl-C

    application.run_polling(allowed_updates=Update.ALL_TYPES)
if __name__ == "__main__":

    _thread = threading.Thread(target=_scraping)
    _thread.start()
    main()
