import os
from flask import Flask, redirect, url_for, request
import requests
from flask_sqlalchemy import SQLAlchemy
import telebot
from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup

global find_groupmates
global find_group

find_groupmates = None
find_group = None

API_KEY = "5047659649:AAHxljzEetaON7tXSqaCiFbNXckHFoHnIrg"
bot = telebot.TeleBot(API_KEY)


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root@localhost:3306/grouptogetherdb'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {'pool_recycle': 299}

db = SQLAlchemy(app)
class Users(db.Model):
    __tablename__ = 'users'

    chat_id = db.Column(db.Integer, nullable=False, primary_key=True)
    name = db.Column(db.String(255), nullable=False)

class Looking_For_Group(db.Model):
    __tablename__ = 'looking_for_group'
    
    chat_id = db.Column(db.Integer, nullable=False, primary_key=True)
    school = db.Column(db.String(100), nullable=False, primary_key=True)
    module_code = db.Column(db.String(100), nullable=False, primary_key=True)
    semester = db.Column(db.Integer, nullable=False,primary_key=True)
    section = db.Column(db.String(100), nullable=False)
    
class Looking_For_Members(db.Model):
    __tablename__ = 'looking_for_members'
    
    chat_id = db.Column(db.Integer, nullable=False, primary_key=True)
    school = db.Column(db.String(100), nullable=False, primary_key=True)
    module_code = db.Column(db.String(100), nullable=False, primary_key=True)
    semester = db.Column(db.Integer, nullable=False,primary_key=True)
    section = db.Column(db.String(100), nullable=False)
    num_members_need = db.Column(db.Integer, nullable=False)
    
class Match_Found(db.Model):
    __tablename__ = 'match_found'
    
    finder_chat_id = db.Column(db.Integer,nullable=False,primary_key=True)
    looker_chat_id = db.Column(db.Integer,nullable=False,primary_key=True)
    school = db.Column(db.String(100), nullable=False, primary_key=True)
    module_code = db.Column(db.String(100), nullable=False, primary_key=True)
    semester = db.Column(db.Integer, nullable=False,primary_key=True)
    section = db.Column(db.String(100), nullable=False)
    accepted = db.Column(db.String(1), nullable=False)
    
def idExists(chat_id):
    # FUNCTION TO CHECK IF USER"S CHAT ID IS IN DATABASE
    users = Users.query.filter_by(chat_id=chat_id)
    for user in users:
        return True
    return False

temp_find_group_dict = {}

class Temp_Find_Group:
    def __init__(self,school):
        self.school = school
        self.module_code = None
        self.semester = None
        self.section = None
        
    def setModuleCode(self,module_code):
        self.module_code = module_code
    def setSemester(self,sem):
        self.module_code = sem
    def setSection(self,section):
        self.section = section
    def getSchool(self):
        return self.school
    def getModuleCode(self):
        return self.module_code
    def getSemester(self):
        return self.semester
    def getSection(self):
        return self.section

bot.set_my_commands([
    BotCommand('start', 'Start finding your groupmates now!'),
])

@bot.message_handler(commands=['start'])
def start(message):
    """
    Command that welcomes the user and configures the initial setup
    """
    chat_id = message.chat.id
    if message.chat.type == 'private':
        chat_user = message.chat.first_name
    else:
        chat_user = message.chat.title
    
    bot.send_sticker(
        chat_id=chat_id, 
        data='CAACAgUAAxkBAAEDoRJh1y0KgigTU87x7QYrbKJNbfDavQACawMAAlobywF60Koi6G4EECME'
    )

    buttons = [
        InlineKeyboardButton(
        text = "Find groupmates",
        callback_data = "Find_groupmates"
    ),
        InlineKeyboardButton(
        text = "Find group",
        callback_data = "Find_group"
    )]
    keyboard = InlineKeyboardMarkup()
    for button in buttons:
        keyboard.add(button)
    message_text = f'Welcome back {chat_user}, Please select if you are finding a group member or looking for a group.'
    bot.send_message(chat_id, message_text, reply_markup = keyboard)

@bot.callback_query_handler(lambda query: query.data == 'Find_groupmates')
def handle_callback(call):
    """
    Handles the execution of the respective functions upon receipt of the callback query
    """
    chat_id = call.message.chat.id

    #bot.register_next_step_handler(msg,confirmEvent)
    pass

@bot.callback_query_handler(lambda query: query.data == 'Find_group')
def handle_callback(call):
    """
    Handles the execution of the respective functions upon receipt of the callback query
    """
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "Please type in your school name (Eg: NUS)")
    bot.register_next_step_handler(msg, enter_school)
    
    

def enter_school(message):
    chat_id = message.chat.id
    school = message.text.upper().strip()
    school_list = ['NUS','NTU','SMU']
    if school not in school_list: 
        msg = bot.reply_to(message,'School is invalid, please try again!')
        bot.register_next_step_handler(msg,enter_school)
        return
    else:
        # new_record = Looking_For_Group(chat_id=chat_id,school=school)
        # db.session.add(new_record)
        # db.session.commit()
        temp_find_group = Temp_Find_Group(school)
        temp_find_group_dict[chat_id] = temp_find_group
        msg = bot.send_message(chat_id, "Please type in your module code (Eg: IS216)")
        bot.register_next_step_handler(msg, enter_module)

def enter_module(message):
    chat_id = message.chat.id
    module = message.text
    print("module",module)
    temp_find_group = temp_find_group_dict[chat_id]
    temp_find_group.setModuleCode(module)
    msg = bot.send_message(chat_id, "Please type in your section (Eg: G11)")
    bot.register_next_step_handler(msg, enter_section)

    
def enter_section(message):
    chat_id = message.chat.id
    section = message.text.strip()
    temp_find_group = temp_find_group_dict[chat_id]
    temp_find_group.setSection(section)
    msg = bot.send_message(chat_id, "Please type in your semester (1 or 2)")
    bot.register_next_step_handler(msg, enter_semester)


def enter_semester(message):
    chat_id = message.chat.id
    semester = message.text
    print("semester",semester)
    temp_find_group = temp_find_group_dict[chat_id]
    temp_find_group.setSemester(semester)
    
    # Add to DB
    new_record = Looking_For_Group(chat_id=chat_id,school=temp_find_group.getSchool(),module_code=temp_find_group.getModuleCode(),semester=temp_find_group.getSemester(),section=temp_find_group.getSection())
    db.session.add(new_record)
    db.session.commit()
    bot.send_message(chat_id, "Your group search request has been successfully created. Now we will search for available groups for you...")
    # Search

def enter_avail(message):
    chat_id = message.chat.id
    
    
bot.infinity_polling()
