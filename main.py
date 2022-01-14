import os
from flask import Flask, redirect, url_for, request
import requests
from flask_sqlalchemy import SQLAlchemy
import telebot
from telebot.types import BotCommand, InlineKeyboardButton, InlineKeyboardMarkup


# Telegram Bot
API_KEY = "" #Telegram API key

bot = telebot.TeleBot(API_KEY) 


app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = '' #token
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
temp_find_member_dict = {}
conversation_dict = {}
accept_dict = {} # Key - (finder,looker), Value - 0, 1, 2 [Represents the number of accepts, with 2 being that both users have accepted]
match_string_dict = {}
temp_data_string_dict = {}

class Temp_Find_Group:
    def __init__(self,school):
        self.school = school
        self.module_code = None
        self.semester = None
        self.section = None
        
    def setModuleCode(self,module_code):
        self.module_code = module_code
    def setSemester(self,sem):
        self.semester = sem
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

class Temp_Find_Member:
    def __init__(self,school):
        self.school = school
        self.module_code = None
        self.semester = None
        self.section = None
        self.num_members_needed = None
        
    def setModuleCode(self,module_code):
        self.module_code = module_code
    def setSemester(self,sem):
        self.semester = sem
    def setSection(self,section):
        self.section = section
    def setNumMembersNeeded(self,num_members_needed):
        self.num_members_needed = num_members_needed
    def getSchool(self):
        return self.school
    def getModuleCode(self):
        return self.module_code
    def getSemester(self):
        return self.semester
    def getSection(self):
        return self.section
    def getNumMembersNeeded(self):
        return self.num_members_needed

bot.set_my_commands([
    BotCommand('start', 'Start finding your groupmates now!'),
    BotCommand('view', 'View your list of groups/members you are finding!'),
    BotCommand('edit', 'Edit your group and/or member search requests!'),
    BotCommand('converse', 'Use this to start talking to someone who has initiate a conversation with you.'),
    BotCommand('search', 'Performs a search for members and groups for all your existing requests.')
])

@bot.message_handler(commands=['start'])
def start(message):
    """
    Command that welcomes the user and configures the initial setup
    """
    chat_id = message.chat.id
    try:
        id_exist = idExists(chat_id)
        if not id_exist:
            bot.send_message(chat_id,"Welcome to GroupTogether, I can help make your project group searching life a breeze.")
            msg = bot.send_message(chat_id,"It looks like it is your first time using me. Please enter your name in the next chat bubble. This name will be saved and used to identify yourself to others.")
            bot.register_next_step_handler(msg,register)
            return
    except:
        print('error went in')
        db.session.rollback()

    '''
    bot.send_sticker(
        chat_id,'CAACAgUAAxkBAAEDoRJh1y0KgigTU87x7QYrbKJNbfDavQACawMAAlobywF60Koi6G4EECME'
    )
    '''
    
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
    message_text = f'Welcome back , Please select if you are finding a group member or looking for a group.'
    bot.send_message(chat_id, message_text, reply_markup = keyboard)
    
def register(message):
    chat_id = message.chat.id
    name = message.text.strip()
    if name == "":
        msg = bot.reply_to(message,'Your name cannot be empty. Please enter your name again!')
        bot.register_next_step_handler(msg,register)
        return
    elif len(name) > 100:
        msg = bot.reply_to(message,"Your name cannot be longer than 100 characters. Please enter your name again!")
        bot.register_next_step_handler(msg,register)
        return
    else:
        new_user = Users(chat_id=chat_id,name=name)
        db.session.add(new_user)
        db.session.commit()
        
        bot.reply_to(message,"Thank you, " + name + ", you have successfully registered.")
        bot.send_sticker(
        chat_id=chat_id, 
        data='CAACAgUAAxkBAAEDoRJh1y0KgigTU87x7QYrbKJNbfDavQACawMAAlobywF60Koi6G4EECME'
        )

        buttons = [
            InlineKeyboardButton(
            text = "Find Members",
            callback_data = "Find_groupmates"
        ),
            InlineKeyboardButton(
            text = "Find Group",
            callback_data = "Find_group"
        )]
        keyboard = InlineKeyboardMarkup()
        for button in buttons:
            keyboard.add(button)
        message_text = f'Now, Please select if you are finding a group member or looking for a group.'
        bot.send_message(chat_id, message_text, reply_markup = keyboard)
    
@bot.message_handler(commands=['view'])
def view(message):
    chat_id = message.chat.id
    
    try:
        id_exist = idExists(chat_id)
        
        flag1 = False
        flag2 = False
        
        if not id_exist:
            start(message)
        else:
            output = ""
            groups = Looking_For_Group.query.filter_by(chat_id = chat_id)
            
            for group in groups:
                flag1 = True
                break
            
            if flag1:
                output += "*Looking for Groups* :\n\n"
                for group in groups:
                    school = group.school
                    module_code = group.module_code
                    semester = group.semester
                    section = group.section
                    output += "School: *" + school + "* "
                    output += "Semester: *" + str(semester) + "* Module: *" + module_code +  "* Section:* " + section + "*\n"
            
            members = Looking_For_Members.query.filter_by(chat_id = chat_id)
            
            for memb in members:
                flag2 = True
                break
            
            if flag2:
                output += "\n *Looking for Members* :\n\n"
                for memb in members:
                    school = memb.school
                    module_code = memb.module_code
                    semester = memb.semester
                    section = memb.section
                    num_mem_need = memb.num_members_need
                    
                    output += "School: *" + school + "* "
                    output += "Semester: *" + str(semester) + "* Module: *" + module_code +  "* Section:* " + section + "* Slots: *"+ str(num_mem_need) + "* \n"
    
            if not flag1 and not flag2:
                bot.send_message(chat_id, "~ Nothing to view ~")
            else:
                bot.send_message(chat_id, output, parse_mode= 'Markdown')
        
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")

# Edit requests made
@bot.message_handler(commands=['edit'])
def editRequests(message):
    chat_id = message.chat.id
    
    try:
        id_exist = idExists(chat_id)
        
        count = 1
        buttons = []
        
        flag1 = False
        flag2 = False
        
        if not id_exist:
            start(message)
        else:
            output = ""
            groups = Looking_For_Group.query.filter_by(chat_id = chat_id)
            
            for group in groups:
                flag1 = True
                break
            
            if flag1:
                output += "*Looking for Groups* :\n\n"
                for group in groups:
                    school = group.school
                    module_code = group.module_code
                    semester = group.semester
                    section = group.section
                    output += str(count) + ". School: *" + school + "* "
                    output += " Semester: *" + str(semester) + "* Module: *" + module_code +  "* Section:* " + section + "*\n"
                    data_string = "-".join([school,module_code,str(semester),section])
                    button = InlineKeyboardButton(
                        text = str(count),
                        callback_data = "edit_group:" + data_string
                    )
                    buttons.append(button)
                    count += 1
            
            members = Looking_For_Members.query.filter_by(chat_id = chat_id)
            
            for memb in members:
                flag2 = True
                break
            
            if flag2:
                output += "\n *Looking for Members* :\n\n"
                for memb in members:
                    school = memb.school
                    module_code = memb.module_code
                    semester = memb.semester
                    section = memb.section
                    num_mem_need = memb.num_members_need
                    
                    output += str(count) + ". School: *" + school + "* "
                    output += "Semester: *" + str(semester) + "* Module: *" + module_code +  "* Section:* " + section + "* Slots: *"+ str(num_mem_need) + "* \n"
                    count += 1
                    data_string = "-".join([school,module_code,str(semester),section,str(num_mem_need)])
                    button = InlineKeyboardButton(
                        text = str(count),
                        callback_data = "edit_mem:" + data_string
                    )
                    buttons.append(button)
    
            if not flag1 and not flag2:
                bot.send_message(chat_id, "You have no requests to edit.")
            else:
                bot.send_message(chat_id, output, parse_mode= 'Markdown')
                keyboard = []
                row_limit = 4
                row = []
                for button in buttons:
                    row.append(button)
                    if len(row) == row_limit:
                        keyboard.append(row)
                        row = []
                if len(row) > 0:
                    keyboard.append(row)
                message_text = f'To edit a search request, please click on the button with the corresponding number to the request you want to edit.'
                bot.send_message(chat_id, message_text, reply_markup = InlineKeyboardMarkup(keyboard),parse_mode= 'Markdown')
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")

@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'edit_group')
def editRequest(query):
    data_string = query.data.split(":")[1]
    chat_id = query.from_user.id
    message_id = query.message.id
    new_markup = InlineKeyboardMarkup([])
    bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    output = "* Looking For Group request *\n\n"
    data_list = data_string.split("-")
    output += "School: *" + data_list[0] + "*\n"
    output += "Module Code: *" + data_list[1] + "*\n"
    output += "Semester: *" + data_list[2] + "*\n"
    output += "Section: *" + data_list[3] + "*\n\n"
    output += "What would you like to do?"
    keyboard = [[InlineKeyboardButton(
                    text = "Delete Request",
                    callback_data = "del_group:" + data_string
                )]]
    bot.send_message(chat_id,output,reply_markup=InlineKeyboardMarkup(keyboard),parse_mode= 'Markdown')
    
@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'del_group')
def delGroup(query):
    data_string = query.data.split(":")[1]
    data_list = data_string.split("-")
    chat_id = query.from_user.id
    message_id = query.message.id
    new_markup = InlineKeyboardMarkup([])
    bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    group_look = Looking_For_Group.query.filter_by(chat_id=chat_id,school=data_list[0],module_code=data_list[1],semester=int(data_list[2]),section=data_list[3]).first()
    db.session.delete(group_look)
    db.session.commit()
    bot.send_message(chat_id,"Request has been deleted successfully!")
    
@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'edit_mem')
def editMem(query):
    data_string = query.data.split(":")[1]
    chat_id = query.from_user.id
    message_id = query.message.id
    new_markup = InlineKeyboardMarkup([])
    bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    output = "* Looking For Member request *\n\n"
    data_list = data_string.split("-")
    output += "School: *" + data_list[0] + "*\n"
    output += "Module Code: *" + data_list[1] + "*\n"
    output += "Semester: *" + data_list[2] + "*\n"
    output += "Section: *" + data_list[3] + "*\n"
    output += "Available Slots: *" + data_list[4] + "*\n"
    output += "What would you like to do?"
    keyboard = [[InlineKeyboardButton(
                    text = "Edit Available Slots",
                    callback_data = "edit_avl:" + data_string
                ),
                InlineKeyboardButton(
                    text = "Delete Request",
                    callback_data = "del_mem:" + data_string
                )]]
    bot.send_message(chat_id,output,reply_markup=InlineKeyboardMarkup(keyboard),parse_mode= 'Markdown')
    
@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'del_mem')
def delGroup(query):
    data_string = query.data.split(":")[1]
    data_list = data_string.split("-")
    chat_id = query.from_user.id
    message_id = query.message.id
    new_markup = InlineKeyboardMarkup([])
    bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    group_look = Looking_For_Members.query.filter_by(chat_id=chat_id,school=data_list[0],module_code=data_list[1],semester=int(data_list[2]),section=data_list[3]).first()
    db.session.delete(group_look)
    db.session.commit()
    bot.send_message(chat_id,"Request has been deleted successfully!")

@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'edit_avl')
def edit_avl(query):
    chat_id = query.from_user.id
    data_string = query.data.split(":")[1]
    temp_data_string_dict[chat_id] = data_string
    message_id = query.message.id
    new_markup = InlineKeyboardMarkup([])
    bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    msg = bot.send_message(chat_id,"Please enter the new available number of slots in your group in the next bubble. Please do NOT indicate 0; delete the request if that is the case.")
    bot.register_next_step_handler(msg,updateAvl)
    
def updateAvl(message):
    chat_id = message.chat.id
    new_num = message.text
    digits = '1234567890'
    # check if its a valid non-zero integer
    for ch in new_num:
        if ch not in digits:
            msg = bot.send_message(chat_id,"Please enter a valid integer again!")
            bot.register_next_step_handler(msg,updateAvl)
            return
    if new_num == "0":
        msg = bot.send_message(chat_id,"Your available slots cannot be zero. Please enter a new number.")
        bot.register_next_step_handler(msg,updateAvl)
        return
    
    data_string = temp_data_string_dict[chat_id]
    data_list = data_string.split("-")
    member_look = Looking_For_Members.query.filter_by(chat_id=chat_id,school=data_list[0],module_code=data_list[1],semester=int(data_list[2]),section=data_list[3]).first()
    member_look.num_members_need = int(new_num)
    db.session.commit()
    bot.send_message(chat_id,"Your available slots has been updated successfully.")
    del temp_data_string_dict[chat_id]
    
    
    

@bot.callback_query_handler(lambda query: query.data == 'Find_groupmates')
def handle_callback(call):
    """
    Handles the execution of the respective functions upon receipt of the callback query Find_groupmates
    """
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "Please type in your school name (Eg: NUS)")
    bot.register_next_step_handler(msg, enter_school2)

@bot.callback_query_handler(lambda query: query.data == 'Find_group')
def handle_callback(call):
    """
    Handles the execution of the respective functions upon receipt of the callback query Find_Group
    """
    chat_id = call.message.chat.id
    msg = bot.send_message(chat_id, "Please type in your school name (Eg: NUS)")
    bot.register_next_step_handler(msg, enter_school1)
    
    

def enter_school1(message):
    chat_id = message.chat.id
    school = message.text.upper().strip()
    school_list = ['NUS','NTU','SMU']
    if school not in school_list: 
        msg = bot.reply_to(message,'School is invalid, please try again!')
        bot.register_next_step_handler(msg,enter_school1)
        return
    else:
        # new_record = Looking_For_Group(chat_id=chat_id,school=school)
        # db.session.add(new_record)
        # db.session.commit()
        temp_find_group = Temp_Find_Group(school)
        temp_find_group_dict[chat_id] = temp_find_group
        msg = bot.send_message(chat_id, "Please type in your module code (Eg: IS216)")
        bot.register_next_step_handler(msg, enter_module1)


def enter_school2(message):
    chat_id = message.chat.id
    school = message.text.upper().strip()
    school_list = ['NUS','NTU','SMU']
    if school not in school_list: 
        msg = bot.reply_to(message,'School is invalid, please try again!')
        bot.register_next_step_handler(msg,enter_school2)
        return
    else:
        # new_record = Looking_For_Group(chat_id=chat_id,school=school)
        # db.session.add(new_record)
        # db.session.commit()
        temp_find_member = Temp_Find_Member(school)
        temp_find_member_dict[chat_id] = temp_find_member
        msg = bot.send_message(chat_id, "Please type in your module code (Eg: IS216)")
        bot.register_next_step_handler(msg, enter_module2)


def enter_module1(message):
    chat_id = message.chat.id
    module = message.text.strip()
    temp_find_group = temp_find_group_dict[chat_id]
    temp_find_group.setModuleCode(module)
    msg = bot.send_message(chat_id, "Please type in your section (Eg: G11)")
    bot.register_next_step_handler(msg, enter_section1)

def enter_module2(message):
    chat_id = message.chat.id
    module = message.text.strip()
    temp_find_member = temp_find_member_dict[chat_id]
    temp_find_member.setModuleCode(module)
    msg = bot.send_message(chat_id, "Please type in your section (Eg: G11)")
    bot.register_next_step_handler(msg, enter_section2)

    
def enter_section1(message):
    chat_id = message.chat.id
    section = message.text.strip()
    temp_find_group = temp_find_group_dict[chat_id]
    temp_find_group.setSection(section)
    msg = bot.send_message(chat_id, "Please type in your semester (1 or 2)")
    bot.register_next_step_handler(msg, enter_semester1)

def enter_section2(message):
    chat_id = message.chat.id
    section = message.text.strip()
    temp_find_member = temp_find_member_dict[chat_id]
    temp_find_member.setSection(section)
    msg = bot.send_message(chat_id, "Please type in your semester (1 or 2)")
    bot.register_next_step_handler(msg, enter_semester2)


def enter_semester1(message):
    try:
        chat_id = message.chat.id
        semester = message.text.strip()
        temp_find_group = temp_find_group_dict[chat_id]
        temp_find_group.setSemester(semester)
        # Add to DB
        new_record = Looking_For_Group(chat_id=chat_id,school=temp_find_group.getSchool(),module_code=temp_find_group.getModuleCode(),semester=temp_find_group.getSemester(),section=temp_find_group.getSection())
        db.session.add(new_record)
        db.session.commit()
        
        msg = bot.send_message(chat_id, "Your group search request has been successfully created. We will search for available groups for you...")
        bot.register_next_step_handler(msg, search1(chat_id))
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")

def enter_semester2(message):
    chat_id = message.chat.id
    semester = message.text.strip()
    temp_find_member = temp_find_member_dict[chat_id]
    temp_find_member.setSemester(semester)
    msg = bot.send_message(chat_id, "Please type how many more members you need to find")
    bot.register_next_step_handler(msg, enter_avail)

def enter_avail(message):
    try:
        chat_id = message.chat.id
        avail = message.text.strip()
        # Add to DB
        temp_find_member = temp_find_member_dict[chat_id]
        temp_find_member.setNumMembersNeeded(avail)
        new_record = Looking_For_Members(chat_id=chat_id,school=temp_find_member.getSchool(),module_code=temp_find_member.getModuleCode(),semester=temp_find_member.getSemester(),section=temp_find_member.getSection(), num_members_need=temp_find_member.getNumMembersNeeded())
        db.session.add(new_record)
        db.session.commit()
        
        msg = bot.send_message(chat_id, "Your group search request has been successfully created. We will search for available members for you...")
        bot.register_next_step_handler(msg, search2(chat_id))
    except:
        db.session.rollback()
    

@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'converse')
def start_convo(query):
    response = query.data.split(":")[1]
    other_chat_id = int(query.data.split(":")[2])
    match_string = query.data.split(":")[3]
    name = Users.query.filter_by(chat_id=other_chat_id)
    chat_id = query.from_user.id
    message_id = query.message.id
    new_markup = InlineKeyboardMarkup([])
    bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    if response == "no":
        # Dont start convo
        bot.send_message(chat_id,"You decided not to have the conversation with " + name + ".")
        new_markup = InlineKeyboardMarkup([])
        bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    else:
        # Check if ongoing convo
        if chat_id in conversation_dict:
            bot.send_message(chat_id,"You are currently in an ongoing conversation, please end this one before continuing another.")
            return
        match_list = match_string.split("-")
        accept_dict[(int(match_list[0]),int(match_list[1]))] = 0
        conversation_dict[chat_id] = other_chat_id
        conversation_dict[other_chat_id] = chat_id
        match_string_dict[other_chat_id] = match_string
        keyboard = [[InlineKeyboardButton("Accept",callback_data='end_convo:accept:' + str(other_chat_id) + ":" + match_string),InlineKeyboardButton("Reject",callback_data='end_convo:reject:' + str(other_chat_id) + ":" + match_string)]]
        markup = InlineKeyboardMarkup(keyboard)
        name = Users.query.filter_by(chat_id=chat_id).first().name
        other_name = Users.query.filter_by(chat_id=other_chat_id).first().name
        msg = bot.send_message(chat_id,'You are now in a conversation with '+ other_name +', Any text you type from here on will be sent to the other person.\n\nIf you have made a decision on whether to team up with the person, click on Accept or Reject to end the conversation.',reply_markup=markup)
        url = 'https://api.telegram.org/bot' + API_KEY + '/sendMessage'
        data = {'chat_id': other_chat_id, 'text': 'We have found a match for you with ' + name + '. To start talking to them, type the command /converse'}
        requests.post(url,data).json()
        bot.register_next_step_handler(msg, converse)

@bot.callback_query_handler(lambda query: query.data.split(":")[0] == 'end_convo')
def endConvo(query):
    chat_id = query.from_user.id
    try:
        response = query.data.split(":")[1]
        other_chat_id = int(query.data.split(":")[2])
        other_name = Users.query.filter_by(chat_id=other_chat_id).first().name
        match_string = query.data.split(":")[3]
        chat_id = query.from_user.id
        name = Users.query.filter_by(chat_id=chat_id).first().name
        message_id = query.message.id
        new_markup = InlineKeyboardMarkup([])
        bot.edit_message_reply_markup(chat_id,message_id,reply_markup=new_markup)
    
    
        if response == "accept":
            # Process acceptance
            match_list = match_string.split("-")
            accept_dict[(int(match_list[0]),int(match_list[1]))] += 1
            bot.send_message(chat_id,"You have accepted the partnership with " + other_name + ". Waiting for them to accept back...")
            url = 'https://api.telegram.org/bot' + API_KEY + '/sendMessage'
            data = {'chat_id': other_chat_id, 'text': name + ' has accepted you.'}
            requests.post(url,data).json()
            
            if accept_dict[(int(match_list[0]),int(match_list[1]))] == 2:
                match_found = Match_Found.query.filter_by(finder_chat_id=int(match_list[0]),looker_chat_id=int(match_list[1]),school=match_list[2],module_code=match_list[3],semester=int(match_list[4]),section=match_list[5]).first()
                match_found.accepted = 'A'
                db.session.commit()
                looking_for_member = Looking_For_Members.query.filter_by(chat_id=int(match_list[0]),school=match_list[2],module_code=match_list[3],semester=int(match_list[4])).first()
                looking_for_member.num_members_need -= 1
                db.session.commit()
                url = 'https://api.telegram.org/bot' + API_KEY + '/sendMessage'
                data = {'chat_id': other_chat_id, 'text': 'Hooray, ' + name + ' has agreed to group together with you for the project. Ending the private conversation.'}
                requests.post(url,data).json()
                bot.send_message(chat_id,"Congratulations! You and " + other_name + " have agreed to group together. Ending private conversation.")
                if looking_for_member.num_members_need == 0:
                    bot.send_message(looking_for_member.chat_id,"Your group is now full! We will be removing your request from our system. Thank you for using GroupTogether!")
                    db.session.delete(looking_for_member)
                    db.session.commit()
                del accept_dict[(int(match_list[0]),int(match_list[1]))]
                del conversation_dict[chat_id]
                del conversation_dict[other_chat_id]
        else:
            match_list = match_string.split("-")
            match_found = Match_Found.query.filter_by(finder_chat_id=int(match_list[0]),looker_chat_id=int(match_list[1]),school=match_list[2],module_code=match_list[3],semester=int(match_list[4]),section=match_list[5]).first()
            match_found.accepted = 'R'
            db.session.commit()
            url = 'https://api.telegram.org/bot' + API_KEY + '/sendMessage'
            data = {'chat_id': other_chat_id, 'text': 'Aww, it looks like ' + name + ' has decided to reject your partnership. Better luck with another person! Ending the private conversation.'}
            requests.post(url,data).json()
            bot.send_message(chat_id,"Awww... It looks like you and  " + other_name + " were just not mean't to be together...in the same group. Ending private conversation.")
            del accept_dict[(int(match_list[0]),int(match_list[1]))]
            del conversation_dict[chat_id]
            del conversation_dict[other_chat_id]
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")

def converse(message):
    
    chat_id = message.chat.id
    try:
        chat_message = message.text
        if chat_id not in conversation_dict:
            bot.send_message(chat_id,"You are not in a conversation!")
        else:
            other_chat_id = conversation_dict[chat_id]
            name = Users.query.filter_by(chat_id=chat_id)
            url = 'https://api.telegram.org/bot' + API_KEY + '/sendMessage'
            data = {'chat_id': other_chat_id, 'text': "From " + name + ": " + chat_message}
            requests.post(url,data).json()
            msg = bot.reply_to(message,"Message sent!")
            print(conversation_dict)
            bot.register_next_step_handler(msg, converse)
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")
        
@bot.message_handler(commands=['converse'])
def startConvo(message):
    
    chat_id = message.chat.id
    try:
        if chat_id not in conversation_dict:
            bot.send_message(chat_id,"You are not in a conversation!")
        else:
            match_string = match_string_dict[chat_id]
            other_chat_id = conversation_dict[chat_id]
            keyboard = [[InlineKeyboardButton("Accept",callback_data='end_convo:accept:' + str(other_chat_id) + ":" + match_string),InlineKeyboardButton("Reject",callback_data='end_convo:reject:' + str(other_chat_id) + ":" + match_string)]]
            markup = InlineKeyboardMarkup(keyboard)
            name = Users.query.filter_by(chat_id=chat_id).first().name
            other_name = Users.query.filter_by(chat_id=other_chat_id).first().name
            msg = bot.send_message(chat_id,'You are now in a conversation with '+ other_name +', Any text you type from here on will be sent to the other person.\n\nIf you have made a decision on whether to team up with the person, click on Accept or Reject to end the conversation.',reply_markup=markup)
            url = 'https://api.telegram.org/bot' + API_KEY + '/sendMessage'
            data = {'chat_id': other_chat_id, 'text': name + ' is now online. You can start talking to them.'}
            requests.post(url,data).json()
            bot.register_next_step_handler(msg,converse)
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")

# Search Code
def search1(chat_id):
    try:
        temp_find_group = temp_find_group_dict[chat_id]
        avl_groups = Looking_For_Members.query.filter_by(school=temp_find_group.getSchool(),module_code=temp_find_group.getModuleCode(),semester=temp_find_group.getSemester(), section=temp_find_group.getSection())
        found = False
        for avl_group in avl_groups:
            found = True
        if not found:
            bot.send_message(chat_id,"Unfortunately, there are currently no matching groups with availability. Please use the /search command again after waiting for some time.")
        else:
            for group in avl_groups:
                other_chat_id = group.chat_id
                name = Users.query.filter_by(chat_id=other_chat_id).first().name
                new_match_found = Match_Found(finder_chat_id=other_chat_id,looker_chat_id=chat_id,school=temp_find_group.getSchool(),module_code=temp_find_group.getModuleCode(),semester=temp_find_group.getSemester(), section=temp_find_group.getSection(),accepted='P')
                db.session.add(new_match_found)
                db.session.commit()
                match_string = '-'.join([str(new_match_found.finder_chat_id),str(new_match_found.looker_chat_id),new_match_found.school,new_match_found.module_code,str(new_match_found.semester),new_match_found.section])
                keyboard = [[InlineKeyboardButton("Yes",callback_data='converse:yes:' + str(other_chat_id) + ":" + match_string),InlineKeyboardButton("No",callback_data='converse:no:' + str(other_chat_id))]]
                markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(chat_id,"We have found an available group for your following group search:\n\nSchool: "+ temp_find_group.getSchool() + "\nModule: " + temp_find_group.getModuleCode() + "\nSemester: " + temp_find_group.getSemester() + "\nSection: " + temp_find_group.getSection() + "\n\nHere are the group details:\n\nContact Person: " + name + "\nAvailable slots: " + str(group.num_members_need) + "\n\nWould you like to start a conversation?" ,reply_markup=markup)
    
        del temp_find_group_dict[chat_id]
    
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")


def search2(chat_id):
    try:
        temp_find_member = temp_find_member_dict[chat_id]
        avl_members = Looking_For_Group.query.filter_by(school=temp_find_member.getSchool(),module_code=temp_find_member.getModuleCode(),semester=temp_find_member.getSemester(), section=temp_find_member.getSection())
        found = False
        for avl_mem in avl_members:
            found = True
        if not found:
            bot.send_message(chat_id,"Unfortunately, there are currently no matching users looking for a group. Please use the /search command again after waiting for some time.")
        else:
            for member in avl_members:
                other_chat_id = member.chat_id
                name = Users.query.filter_by(chat_id=other_chat_id).first().name
                new_match_found = Match_Found(finder_chat_id=chat_id,looker_chat_id=other_chat_id,school=temp_find_member.getSchool(),module_code=temp_find_member.getModuleCode(),semester=temp_find_member.getSemester(), section=temp_find_member.getSection(),accepted='P')
                db.session.add(new_match_found)
                db.session.commit()
                match_string = '-'.join([str(new_match_found.finder_chat_id),str(new_match_found.looker_chat_id),new_match_found.school,new_match_found.module_code,str(new_match_found.semester),new_match_found.section])
                keyboard = [[InlineKeyboardButton("Yes",callback_data='converse:yes:' + str(other_chat_id) + ":" + match_string),InlineKeyboardButton("No",callback_data='converse:no:' + str(other_chat_id))]]
                markup = InlineKeyboardMarkup(keyboard)
                bot.send_message(chat_id,"We have found an available member for your following member search:\n\nSchool: "+ temp_find_member.getSchool() + "\nModule: " + temp_find_member.getModuleCode() + "\nSemester: " + temp_find_member.getSemester() + "\nSection: " + temp_find_member.getSection() + "\n\nHere are their details:\n\nContact Person: " + name + "\n\nWould you like to start a conversation?" ,reply_markup=markup)
            
        del temp_find_member_dict[chat_id]
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")
    
@bot.message_handler(commands=['search'])
def performSearch(message):
    # Perform group search
    chat_id = message.chat.id
    try:
        looking_for_group_list = Looking_For_Group.query.filter_by(chat_id=chat_id)
        group_found = False
        for l in looking_for_group_list:
            group_found = True
            break
        if group_found:
            bot.send_message(chat_id,"Searching for groups based on your requests...")
            count = 0
            for group_look in looking_for_group_list:
                avl_groups = Looking_For_Members.query.filter_by(school=group_look.school,module_code=group_look.module_code,semester=group_look.semester, section=group_look.section)
                for group in avl_groups:
                    other_chat_id = group.chat_id
                    name = Users.query.filter_by(chat_id=other_chat_id).first().name
                    # check if match_Found exists
                    new_match_found = Match_Found.query.filter_by(finder_chat_id=other_chat_id,looker_chat_id=chat_id,school=group_look.school,module_code=group_look.module_code,semester=group_look.semester, section=group_look.section).first()
                    if not new_match_found:
                        new_match_found = Match_Found(finder_chat_id=other_chat_id,looker_chat_id=chat_id,school=group_look.school,module_code=group_look.module_code,semester=group_look.semester, section=group_look.section,accepted='P')
                        db.session.add(new_match_found)
                        db.session.commit()
                    match_string = '-'.join([str(new_match_found.finder_chat_id),str(new_match_found.looker_chat_id),new_match_found.school,new_match_found.module_code,str(new_match_found.semester),new_match_found.section])
                    keyboard = [[InlineKeyboardButton("Yes",callback_data='converse:yes:' + str(other_chat_id) + ":" + match_string),InlineKeyboardButton("No",callback_data='converse:no:' + str(other_chat_id))]]
                    markup = InlineKeyboardMarkup(keyboard)
                    bot.send_message(chat_id,"We have found an available group for your following group search:\n\nSchool: "+ group_look.school + "\nModule: " + group_look.module_code + "\nSemester: " + str(group_look.semester) + "\nSection: " + group_look.section + "\n\nHere are the group details:\n\nContact Person: " + name + "\nAvailable slots: " + str(group.num_members_need) + "\n\nWould you like to start a conversation?" ,reply_markup=markup)
                    count += 1
                    
            if count == 0:
                bot.send_message(chat_id,"Sorry, it looks like that there are no available groups that match your requests.")
        
        # Perform Member search
        looking_for_member_list = Looking_For_Members.query.filter_by(chat_id=chat_id)
        member_found = False
        for l in looking_for_member_list:
            member_found = True
            break
        if member_found:
            bot.send_message(chat_id,"Searching for members based on your requests...")
            count = 0
            for member_look in looking_for_member_list:
                avl_groups = Looking_For_Group.query.filter_by(school=member_look.school,module_code=member_look.module_code,semester=member_look.semester, section=member_look.section)
                for group in avl_groups:
                    other_chat_id = group.chat_id
                    name = Users.query.filter_by(chat_id=other_chat_id).first().name
                    new_match_found = Match_Found.query.filter_by(finder_chat_id=chat_id,looker_chat_id=other_chat_id,school=member_look.school,module_code=member_look.module_code,semester=member_look.semester, section=member_look.section).first()
                    if not new_match_found:
                        new_match_found = Match_Found(finder_chat_id=chat_id,looker_chat_id=other_chat_id,school=member_look.school,module_code=member_look.module_code,semester=member_look.semester, section=member_look.section,accepted='P')
                        db.session.add(new_match_found)
                        db.session.commit()
                    match_string = '-'.join([str(new_match_found.finder_chat_id),str(new_match_found.looker_chat_id),new_match_found.school,new_match_found.module_code,str(new_match_found.semester),new_match_found.section])
                    keyboard = [[InlineKeyboardButton("Yes",callback_data='converse:yes:' + str(other_chat_id) + ":" + match_string),InlineKeyboardButton("No",callback_data='converse:no:' + str(other_chat_id))]]
                    markup = InlineKeyboardMarkup(keyboard)
                    bot.send_message(chat_id,"We have found an available member for your following member search:\n\nSchool: "+ member_look.school + "\nModule: " + member_look.module_code + "\nSemester: " + str(member_look.semester) + "\nSection: " + member_look.section + "\n\nHere are their details:\n\nContact Person: " + name + "\n\nWould you like to start a conversation?" ,reply_markup=markup)
                    count += 1
                    
            if count == 0:
                bot.send_message(chat_id,"Sorry, it looks like that there are no available members that match your requests.")
                
    except:
        bot.send_message(chat_id, "Sorry you have been inactive for a long time. Please /start again")

bot.infinity_polling()