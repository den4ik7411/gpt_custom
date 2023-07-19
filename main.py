
# NOW, BOT IS WORKING! BUT IT IS PROTOTYPE

from aiogram import Bot, Dispatcher, executor, types
import json, openai, sqlite3, time
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup



API_TOKEN = ''
openai.api_key = ""

bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot, storage=MemoryStorage())

class States(StatesGroup):
    char_n = State()
    char = State()

users = {}
character = []
time1 = time.time()

default = [{"role": "system", "content": "pretend youre a cute anime girl who talks in all lowercase, doesnt use punctuation, uses a tilda at the end of every sentence, and uses LOTS of emoticons."}]

default_n = ""
welcome = """
Welcome to Adolf!
Here you can custom your chat process with: 

  /new - erase the dialogue history
  /char - send text prompt for change GPT character
Type text prompt to start
  """#/char - send text prompt for change GPT character         IN THE NEXT UPDATES
  #/add - add your character's prompt to char menu

conn = sqlite3.connect('db.db')
c = conn.cursor()
c.execute('''
          CREATE TABLE IF NOT EXISTS users
          ([usr_id] INTEGER PRIMARY KEY, [hist] INTEGER)
          ''')


def LoadUsers():
    global users
    global conn
    global c
    conn = sqlite3.connect('db.db')
    c = conn.cursor()
    c.execute("""SELECT * from users""")
    records = c.fetchall()
    for r in records:
        users[r[0]] = {}
        users[r[0]]['hist'] = r[1]


LoadUsers()

def create_user(user: int, num: int):
    global conn
    users[user] = {}
    users[user]['hist'] = num

    sqlite_insert_with_param = '''
          INSERT INTO users (usr_id, hist)

                VALUES
                (?, ?);
          '''

    data_tuple = (user, num)
    c.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()
    with open('data.json', 'r', encoding='utf8') as fr:
        try:
            usr_data = list(json.load(fr))
            usr_data.append({"hist":  default})
        except:
            usr_data = [{"hist": default}]
    with open('data.json', 'w', encoding='utf8') as fg:
        json.dump(usr_data, fg, ensure_ascii=False, indent=2)

def check_time():
    global time1
    time1 = time.time()

char_b = KeyboardButton('/char')
kb = ReplyKeyboardMarkup.add(char_b)

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    if message.from_user.id not in users:
        create_user(int(message.from_user.id), len(c.fetchall()))
    await bot.send_message(chat_id=message.from_user.id, text=welcome)

@dp.message_handler(commands=['char'])
async def char(message: types.Message):
    await bot.send_message(chat_id = message.from_user.id, text ="Choose a personality of GPT: \n"
                                                                 "(Send name at first)", reply_markup=kb)
    await States.char_n.set()

@dp.message_handler(state=States.char_n)
async def char_n_change(message: types.Message, state: FSMContext):
    global character
    character = [str(message.text)]
    await state.finish()
    await bot.send_message(chat_id=message.from_user.id, text="Character name changed. \n"
                                                              "(Send prompt for gpt's character)")
    await States.char.set()

@dp.message_handler(state=States.char)
async def char_change(message: types.Message, state: FSMContext):
    character.append(str(message.text))
    await state.finish()

@dp.message_handler(commands=['new'])
async def new_dialog(message: types.Message):
    num = int(users[message.from_user.id]["hist"])
    with open('data.json', 'r', encoding='utf8') as fr:
        usr_data = list(json.load(fr))
        usr_data[num]["hist"] = default
    with open('data.json', 'w', encoding='utf8') as fw:
        json.dump(usr_data, fw, ensure_ascii=False, indent=2)
    await message.answer("Memory cleared")

@dp.message_handler(content_types=["text"])
async def gpt_working(message: types.Message):
    time0 = time.time()
    if time0 - time1 < 4:
        await message.answer("Don't send requests so fast. \nPlease try again in 20 seconds")
    else:
        try:
            print(time0-time1)
            with open('data.json', 'r', encoding='utf8') as fr:
                gpt_prompt = json.load(fr)
                gpt_prompt[users[message.from_user.id]["hist"]]["hist"].append({'role':"user", "content": f"{message.text}"})
                with open('data.json', 'w', encoding='utf8') as fw:
                    json.dump(gpt_prompt, fw, ensure_ascii=False, indent=2)
            with open('data.json', 'r', encoding='utf8') as fr:
                gpt_prompt = json.load(fr)
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=list(gpt_prompt[users[message.from_user.id]["hist"]]["hist"]))
            response = response["choices"][0]["message"]["content"]
            await message.answer(response, reply_markup=kb)                 )
            gpt_prompt[int(users[message.from_user.id]["hist"])]['hist'].append({"role": "assistant", "content": f"{response}"})
            with open('data.json', 'w', encoding='utf8') as fg:
                json.dump(gpt_prompt, fg, ensure_ascii=False, indent=2)
            character.clear()
            check_time()
        except Exception:
            await bot.send_message(chat_id=message.from_user.id, text='Error generating response. Please try later.')


if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
