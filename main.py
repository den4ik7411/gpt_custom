import json
import openai
import sqlite3
import time

from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton

API_TOKEN = ''
openai.api_key = ''

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
Welcome to GPT-3 customizer bot!
Here you can customize your chat process with: 

  CREATE - create your GPT character
  NEW - erase dialog history
  CHOOSE - change your GPT character
  
Type text prompt to start
"""
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
    print(f'Users: {len(records)}')
    for r in records:
        users[r[0]] = {}
        users[r[0]]['hist'] = r[1]
    return len(records)
LoadUsers()

def create_user(user: int, num: int):
    global conn
    users[user] = {}
    users[user]['hist'] = num
    sqlite_insert_with_param = '''
          INSERT INTO users (usr_id, hist) VALUES (?, ?);'''
    data_tuple = (user, num)
    c.execute(sqlite_insert_with_param, data_tuple)
    conn.commit()
    with open('data.json', 'r', encoding='utf8') as fr:
        try:
            usr_data = list(json.load(fr))
            usr_data.append({"hist":  default, "char": []})
        except:
            usr_data = [{"hist": default, "char": []}]
    with open('data.json', 'w', encoding='utf8') as fg:
        json.dump(usr_data, fg, ensure_ascii=False, indent=2)

def check_time():
    global time1
    time1 = time.time()

def clear_hist(num, change, char_num):
    with open('data.json', 'r', encoding='utf8') as fr:
        usr_data = list(json.load(fr))
        if change == False:
            usr_data[num]["hist"] = default
        else:
            usr_data[num]["hist"] = [{"role":"system", "content":usr_data[num]["char"][char_num]["prompt"]}]
        with open('data.json', 'w', encoding='utf8') as fw:
            json.dump(usr_data, fw, ensure_ascii=False, indent=2)

create_b = InlineKeyboardButton(text='CREATE', callback_data='create')
new_b = InlineKeyboardButton(text='NEW', callback_data='new')
char_b = InlineKeyboardButton(text='CHOOSE', callback_data='char')
show_b = InlineKeyboardButton(text="SHOW PROMPT",callback_data="show")
del_b = InlineKeyboardButton(text="DELETE", callback_data="delete")
menu = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True).add(KeyboardButton(text="/menu"))
kb = InlineKeyboardMarkup().add(create_b,new_b,char_b)
del_kb = InlineKeyboardMarkup().add(del_b).add(create_b,new_b,char_b)
show_kb = InlineKeyboardMarkup().add(show_b, del_b).add(create_b,new_b,char_b)

@dp.message_handler(commands=['start', 'menu'])
async def send_welcome(message: types.Message):
    if message.from_user.id not in users:
        create_user(int(message.from_user.id), LoadUsers())
    await message.delete()
    await message.answer(welcome, reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('create'))
async def create_cb(message: types.CallbackQuery):
    global last_msg
    with open('data.json', 'r', encoding='utf8') as fr:
        usr_data = list(json.load(fr));i = 0;chrs = []
    while i != len(usr_data[int(users[message.from_user.id]["hist"])]['char']):
        chrs.append({"name": usr_data[int(users[message.from_user.id]["hist"])]['char'][i]['name'],
                      "prompt": usr_data[int(users[message.from_user.id]["hist"])]['char'][i]["prompt"]})
        i += 1
    if len(chrs) == 5:
        await message.message.edit_text("You cannot create more than five characters", reply_markup=kb)
    else:
        last_msg = await message.message.edit_text("Send name at first\n(no more than 25 symbols)")
        await States.char_n.set()

@dp.message_handler(state=States.char_n)
async def char_n_change(message: types.Message, state: FSMContext):
    global character, last_msg
    if len(message.text) <= 25:
        character = [str(message.text)]
        await state.finish()
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await message.answer(f"Name: {message.text}. Send prompt for gpt's personality\n(no more than 250")
        await States.char.set()
    else:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await message.answer("Write name shorter than 25 symbols: ")

@dp.message_handler(state=States.char)
async def char_change(message: types.Message, state: FSMContext):
    if len(message.text) <= 250:
        character.append(str(message.text))
        await state.finish()
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await message.answer("Character created", reply_markup=kb)
        with open('data.json', 'r', encoding='utf8') as fr:
            usr_data = list(json.load(fr))
            usr_data[int(users[message.from_user.id]["hist"])]['char'].append({"name":f"{character[0]}",
                                                                               "prompt":f"{character[1]}"})
            with open('data.json', 'w', encoding='utf8') as fw:
                json.dump(usr_data, fw, ensure_ascii=False, indent=2)
        character.clear()
    else:
        await bot.delete_message(chat_id=message.from_user.id, message_id=message.message_id)
        await message.answer("Write prompt shorter than 250 symbols: ")

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('delete'))
async def delete_char(message: types.CallbackQuery):
    try:
        with open('data.json', 'r', encoding='utf8') as fr:
            usr_data = list(json.load(fr)); i = 0
            for j in usr_data[int(users[message.from_user.id]["hist"])]['char']:
                if j == chars[0]:
                    usr_data[int(users[message.from_user.id]["hist"])]['char'].pop(i)
                i += 1
            with open('data.json', 'w', encoding='utf8') as fw:
                json.dump(usr_data, fw, ensure_ascii=False, indent=2)
        clear_hist(int(users[message.from_user.id]["hist"]), False, None)
        await message.message.edit_text("Personality was delete", reply_markup=kb)
    except:
        await message.message.edit_text("Error. Please try again later", reply_markup=kb)
        chars.clear()

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('new'))
async def new_cb(message: types.CallbackQuery):
    clear_hist(int(users[message.from_user.id]["hist"]), False, None)
    await message.message.edit_text("Memory cleared", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('char'))
async def char_cb(message: types.CallbackQuery):
    try:
        with open('data.json', 'r', encoding='utf8') as fr:
            usr_data = list(json.load(fr))
        global chars
        chars = [];names = "";i = 0
        choose_kb = InlineKeyboardMarkup()
        while i != len(usr_data[int(users[message.from_user.id]["hist"])]['char']):
            chars.append({"name":usr_data[int(users[message.from_user.id]["hist"])]['char'][i]['name'],
                          "prompt":usr_data[int(users[message.from_user.id]["hist"])]['char'][i]["prompt"]})
            ch_name = chars[i]["name"]
            names += f"{i+1} - {ch_name} \n"
            x = InlineKeyboardButton(f"{i+1}", callback_data=str(i))
            choose_kb.add(x)
            i += 1
        if chars == []:
            await message.message.edit_text("You don't have any personalities", reply_markup=kb)
        else:
            await message.message.edit_text(f"Your personalities:\n\n{names}\n  Type number of personality to choose",
                                         reply_markup=choose_kb)
    except:
        await message.message.edit_text("Error. Please try again later", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data and c.data.startswith('show'))
async def show_cb(message: types.CallbackQuery):
    name = chars[0]["name"]
    prompt = chars[0]["prompt"]
    await message.message.edit_text(f"{name} : {prompt}", reply_markup=del_kb)

@dp.callback_query_handler(lambda c: c.data)
async def char_choose_cb(message: types.CallbackQuery):
    try:
        i = 0
        clear_hist(int(users[message.from_user.id]["hist"]), True, int(message.data))
        while i <= len(chars):
            for j in chars:
                if i == int(message.data):
                    char = chars[i]
                    chars.clear()
                    chars.append(char)
                i += 1
        await message.message.edit_text(f"You choose  :  {char['name']}", reply_markup=show_kb)
    except:
        await message.message.edit_text("Type correct number of personality or try again later", reply_markup=kb)

@dp.message_handler(content_types=["text"])
async def gpt_working(message: types.Message):
    time0 = time.time()
    if time0 - time1 < 4:
        await message.answer("Don't send requests so fast. \nPlease try again in 20 seconds")
    else:
        try:
            with open('data.json', 'r', encoding='utf8') as fr:
                gpt_prompt = list(json.load(fr))
                gpt_prompt[int(users[message.from_user.id]["hist"])]["hist"].append({'role':"user", "content": f"{message.text}"})
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=list(gpt_prompt[users[message.from_user.id]["hist"]]["hist"]))
            response = response["choices"][0]["message"]["content"]
            await message.answer(response, reply_markup=menu)
            gpt_prompt[int(users[message.from_user.id]["hist"])]['hist'].append({"role": "assistant", "content": f"{response}"})
            with open('data.json', 'w', encoding='utf8') as fg:
                json.dump(gpt_prompt, fg, ensure_ascii=False, indent=2)
            check_time()
        except:
            await message.answer('Error generating response. Please try later.', reply_markup=kb)

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
