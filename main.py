
# NOW, BOT ISN'T WORKING! IT'S PROTOTYPE

from aiogram import Bot, Dispatcher, executor, types
import json, openai, sqlite3
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup


API_TOKEN = ''
openai.api_key = ""
default = [{"role": "system", "content": "ENTER GPT'S CHARACTER HERE"}]

bot_name = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())


class States(StatesGroup):
    char_n = State()
    char = State()

users = {}
queue = []

default = [{"role": "system", "content": "ENTER GPT'S CHARACTER HERE"}]

default_n = ""
welcome = f"""
Welcome to {bot_name}!
Here you can custom your chat process with: 

  /new - erase the dialogue history
  /char - send text prompt for change GPT character

Type text prompt to start
  """

conn = sqlite3.connect('db.db')
c = conn.cursor()
c.execute('''
          CREATE TABLE IF NOT EXISTS users
          ([usr_id] INTEGER PRIMARY KEY, [char_n] TEXT, [char] TEXT, [hist] TEXT)
          ''')


def LoadUsers():
    global conn
    global c
    global users

    sqlite_select_query = """SELECT * from users"""
    c.execute(sqlite_select_query)
    records = c.fetchall()
    print("Total rows are:  ", len(records))
    for r in records:
        users[r[0]] = {}
        users[r[0]]['char_n'] = r[1]
        users[r[0]]['char'] = r[2]
        users[r[0]]['hist'] = r[3]

LoadUsers()


def create_user(user: int, char_n: str, char: str, hist: str):
    global conn
    users[user] = {}
    users[user]['char_n'] = char_n
    users[user]['char'] = char
    users[user]['hist'] = hist

    sqlite_insert_with_param = '''
          INSERT INTO users (usr_id, char_n, char, hist)

                VALUES
                (?, ?, ?, ?);
          '''

    data_tuple = (user, char_n, char, hist)
    c.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()

def updateUser(user: int, char_n: str, char: str, hist: str):
    global conn
    global c
    sqlite_update_query = """Update users set char_n = ?, char = ?, hist = ? where usr_id = ?"""

    columnValues = (
        char_n, char, hist,user)
    c.execute(sqlite_update_query, columnValues)
    conn.commit()

def str2mASSive(user: int, string: str, role: str):
    result = [{'role': f'{role}', 'content': f'{string}'}]
    if users[user]['hist'] == "":
        return result
    else:
        return result.append({})

char_b = KeyboardButton('/char')
kb = ReplyKeyboardMarkup.add(char_b)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id not in users:
        create_user(message.from_user.id, default_n, default)
    await bot.send_message(chat_id=message.from_user.id, text=welcome)

@dp.message_handler(commands=['char'])
async def char(message: types.Message):
    await bot.send_message(chat_id = message.from_user.id, text ="Choose a personality of GPT: \n"
                                                                 "(Send name at first)", reply_markup=kb)
    await States.char.set()

@dp.message_handler(state=States.char)
async def char_n_change(message: types.Message, state: FSMContext):
    users[message.from_user.id]['char_n'] = str(message.text)
    #updateUser(message.from_user.id)
    await state.finish()
    await bot.send_message(chat_id=message.from_user.id, text="Character name changed. \n"
                                                              "(Send prompt for gpt's character)")
    await States.char_n.set()

@dp.message_handler(state=States.char_n)
async def char_change(message: types.Message, state: FSMContext):
    users[message.from_user.id]['char'] = str(message.text)
    await state.finish()

@dp.message_handler(commands=['dump'])
async def dump_db(message: types.Message):
    if message.from_user.id == 1584001368:
        try:
            await message.reply_document(open('db.db', 'rb'), reply_markup=kb)
        except Exception:
            print(OSError)

@dp.message_handler(commands=['new'])
async def new_dieeee(message: types.Message):
    with open('data.json', 'w', encoding='utf8') as fw:
        json.dump(default, fw, ensure_ascii=False)
    await message.answer("Memory cleared")


@dp.message_handler(content_types=["text"])
async def gpt_working(message: types.Message):
    with open('data.json', 'r', encoding='utf8') as fr:
        gpt_prompt = json.load(fr)
   
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=gpt_prompt)
    response = response["choices"][0]["message"]["content"]
    await message.answer(response, reply_markup=kb)
    gpt_prompt.append({"role": "assistant", "content": f"{response}"})
    with open('data.json', 'w', encoding='utf8') as fg:
        json.dump(gpt_prompt, fg, ensure_ascii=False)
    

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
