from flask import *
from flask_mysqldb import MySQL
import database as database
import re, hashlib
import os
import uuid
from ocr_core import ocr_core
from chat import chat, rag, image_text
from flask import request
import myModule as myModule
from werkzeug.utils import secure_filename
from datetime import datetime
import json as json
from fpdf import FPDF
import unidecode
import re
import globals



public = Blueprint('public', __name__)

# public.register_blueprint(public)
# app.config['MYSQL_HOST'] = 'localhost'
# app.config['MYSQL_USER'] = 'root'
# app.config['MYSQL_PASSWORD'] = ''
# app.config['MYSQL_DB'] = 'test'
# mysql = MySQL(public)


@public.route("/")
def root():
    return redirect('/index')

@public.route('/index')
def landingPage():
    return render_template('index.html')

@public.route('/ocr')
def OCRpage():
    userData = database.select("SELECT * FROM user")
    if(session.get('user')) : return render_template('ocr.html', userData = userData, userLoginStatus = True)
    return render_template('ocr.html', userData = userData, userLoginStatus = False)

@public.route('/share', methods=['POST', 'GET'])
def share():
    if(session.get('user')):
        if(request.method == 'POST'):
            user = session.get('user')
            receiverList = request.form.get('userList')
            text = str(request.form.get('text'))
            fileName = request.form.get('fileName')
            fileFormat = request.form.get('fileFormat')
            
            receiverListNew = json.loads(receiverList)
            
            for receiver in receiverListNew :                 
                database.insert("INSERT INTO message SET sender_id='%s', receiver_id='%s', text='%s', file_name='%s', file_type='%s'" % (user, receiver, text, fileName, fileFormat))

            return 'success'
        else: return 'get method is called, post required'


@public.route('/message', methods = ['POST', 'GET'])
def message():
    if session.get('user'):
        today = datetime.now().strftime("%d-%m-%Y")
        userListQuery = "SELECT * FROM user"
        userData = database.select(userListQuery)
        chats = database.select("SELECT * FROM message")
        return render_template('message.html', userData = userData, chats = chats, today = today)
    return root()

@public.route('/sendMessage', methods = ['POST', 'GET'])
def sendMessage():
    if request.method == 'POST':
        message = request.form.get('message')
        sender = session.get('user')
        receiver = request.form.get('receiver')
        
        database.insert("INSERT INTO message SET sender_id='%s', receiver_id='%s', text='%s'" % (sender, receiver, message))
        return 'success'
        
@public.route('/post')
def post(): 
    text = ''
    if session.get('post') :
        text = session.get('post')
        session['post'] = None
    return render_template('post.html', text = text) 

@public.route('/addPost', methods = ['POST', 'GET'])
def addPost(): 
    if(session.get('user')) :
        userId = session.get('user_id')
        caption = request.form.get('caption')
        content = request.form.get('content')
        
        x = ['', '']
        if caption == '' or caption == None :
            x[0] = 'caption should not be empty'
        if content == '' or content == None :
            x[1] = 'content should not be empty'
        for val in x :
           if val != '' : return x
           
        caption = caption.replace("'", "\\'")
        content = content.replace("'", "\\'")
        
        database.insert("INSERT INTO post SET user_id='%s', caption='%s', content='%s'" % (userId, caption, content))
        return 'success'
    else :
        return 'not logged in'
    
@public.route('/getPosts', methods = ['POST', 'GET'])
def getPosts() : 
    userId = session.get('user_id') or 0
    return [database.select("SELECT post.*, user.username, user.name, user.profile_pic FROM post JOIN user ON post.user_id = user.user_id ORDER BY post.post_id DESC"), userId]
    
@public.route('/getPostsSelf', methods = ['POST', 'GET'])
def getPostsOwn() : 
    if(session.get("user")) :
        userId = session.get('user_id')
        return database.select("SELECT post.*, user.username, user.name, user.profile_pic FROM post JOIN user ON post.user_id = user.user_id WHERE post.user_id='%s' ORDER BY post.post_id DESC" % (userId))
    else : return redirect('/index')
    

@public.route('/profile')
def profile():
    if(session.get('user')):
        userId = session.get('user')
        ud = database.select("SELECT * FROM user")
        userData = database.select("SELECT * FROM user where user_id='%s'" % (userId))
        history = database.select("SELECT * FROM text WHERE user_id='%s' ORDER BY text_id DESC" % (userId))
        return render_template('profile.html', userData = userData, ud = ud, history = history)

@public.route('/updateText', methods = ["POST", "GET"])
def updateText():
    if session.get('user'):
        if request.method == 'POST':
            textId = request.form.get('textId')
            textContent = request.form.get('textContent')
            database.update("UPDATE text SET new_text='%s', last_edited=NOW() WHERE text_id='%s'" % (textContent, textId))
            return 'success'
        else: 
            return redirect('/index')
    else:
        return redirect('/login')

@public.route('/resend', methods = ["POST", "GET"])
def resend():
    if session.get('user'):
        if request.method == 'POST':
            textId = request.form.get('textId')
            database.update("UPDATE text SET file_given_done='0' WHERE text_id='%s'" % (textId))
            return 'success'
        else: 
            return redirect('/index')
    else:
        return redirect('/login')

@public.route('/updateProfile', methods = ['POST', 'GET'])
def updateProfile():
    if session.get('user'):
        if request.method == 'POST' :
            userId = session.get('user')
            name = request.form.get('name')
            gender = request.form.get('gender')
            address = request.form.get('address')
            email = request.form.get('email')
            phone = request.form.get('phone')
            username = request.form.get('username')
            submit = request.form.get('submit')
            
            
            x = ['', '', '', '', '']
            y = x
            
            if name == None or name == "" :
                name = ""
                x[0] = 'please enter a name' 
                
            if address == None or address == "" :
                address = ""
                x[1] = 'please enter an address'
                
            if phone == None or phone == "" :
                phone = ""
                x[2] = 'please enter a phone number'
            elif not re.fullmatch(r'^[0-9]{10}$', phone) :
                x[2] = 'invalid phone number...!'
                
            if email == None or email == "" :
                email = ""
                x[3] = 'please enter an email'
            elif not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email) :
                x[3]  = 'invalid email id...!'
            
            selectUsernameAndPasswordQuery = "SELECT user_id, username, password FROM user WHERE username='"+ username +"' && user_id!='"+ str(userId) +"'"
            result = database.select(selectUsernameAndPasswordQuery)
            if username == None or username == "" :
                username = ""
                x[4] = 'please enter a username'
            elif len(result) > 0 :
                x[4] = 'username has been already taken...!'
                    
            for val in x :
                if val == '' :
                    continue
                else :
                    return x
            if submit == 'true' :
                q = "UPDATE user SET username='" + username + "', name='" + name + "', gender='" + gender + "', address='" + address + "', phone='" + phone + "', email='" + email + "' WHERE user_id='" + str(userId) + "'"
                result = database.insert(q)
                return 'success'
            else : return y
    return 'failed'

@public.route('/login', methods = ['POST', 'GET'])
def login():
    if request.method == 'POST':
        x = ['', '']
        username = request.form.get('username')
        password = request.form.get('password')
        if username == None or username == "":
            x[0] = "enter the username"
            return x
        selectUserAndPasswordQuery = "SELECT user_id, username, password, 'user' as userType FROM user WHERE username='"+ username +"' UNION ALL SELECT id, username, password, 'deo' as userType FROM deo WHERE username='"+ username +"'"
        result = database.select(selectUserAndPasswordQuery)
        if len(result) > 0 :
            if password == None or password == "" :
                x[1] = "enter the password"
                return x
            # password = (hashlib.md5(password.encode())).hexdigest()
            if result[0]['password'] == password :
                if result[0]['userType'] == 'user' :
                    session['user'] = result[0]['user_id']
                    return 'user'
                else : 
                    status = (database.select("SELECT status FROM deo WHERE id='%s'" % (result[0]['user_id'])))[0]['status']
                    if status == 0 :
                        return 'DNV'
                    blockedStatus = (database.select("SELECT block FROM deo WHERE id='%s'" % (result[0]['user_id'])))[0]['block']
                    if blockedStatus == 1 :
                        return 'blocked'
                    session['deo'] = result[0]['user_id']
                    return 'deo'
            else :
                x[1] = 'wrong password'
                return x
        else : 
            x[0] = 'invalid username'
            return x
    return render_template('login.html')

@public.route('/logout')
def logout():
    session['user'] = None
    return 'success'

@public.route('/registration', methods = ['POST', 'GET'])
def registration():
    if request.method == 'POST' :
        name = request.form.get('name')
        userType = request.form.get('userType')
        gender = request.form.get('gender')
        address = request.form.get('address')
        email = request.form.get('email')
        phone = request.form.get('phone')
        username = request.form.get('username')
        password = request.form.get('password')
        confirm_password = request.form.get('confirmPassword')
        submit = request.form.get('submit')
        
        
        userType = "user" if userType == "user" else "deo"

        x = ['', '', '', '', '', '', '']
        y = x
        
        if name == None or name == "" :
            name = ""
            x[0] = 'please enter a name' 
             
        if address == None or address == "" :
            address = ""
            x[1] = 'please enter an address'
            
        if phone == None or phone == "" :
            phone = ""
            x[2] = 'please enter a phone number'
        elif not re.fullmatch(r'^[0-9]{10}$', phone) :
            x[2] = 'invalid phone number...!'
            
        if email == None or email == "" :
            email = ""
            x[3] = 'please enter an email'
        elif not re.fullmatch(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', email) :
            x[3]  = 'invalid email id...!'
        
        selectUsernameAndPasswordQuery = "SELECT username, password FROM user WHERE username='"+ username +"' UNION SELECT username, password FROM deo WHERE username='"+ username +"'"
        result = database.select(selectUsernameAndPasswordQuery)
        if username == None or username == "" :
            username = ""
            x[4] = 'please enter a username'
        elif len(result) > 0 :
            x[4] = 'username has been already taken...!'
            
        if confirm_password == None or confirm_password == "" :
            confirm_password = ""
        if password == None or password == "" :
            password = ""
            x[5] = 'please enter a password'
        elif not re.fullmatch(r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{6,}$', password) :
            x[5] = 'read the note below'
        else : 
            if password == confirm_password :
                x[6] = ''
            else :
                x[6] = 'enter the password again' 
                
        for val in x :
           if val == '' :
               continue
           else :
               return x
        if submit == 'true' :
            # password = (hashlib.md5(password.encode())).hexdigest()
            q = "INSERT INTO "+ userType +" SET username='"+ username +"', password='"+ password +"', name='"+name+"', gender='"+gender+"', address='"+address+"', phone='"+phone+"', email='"+email+"'"
            result = database.insert(q)
            return 'success'
        else : return y
    return render_template('registration.html')

@public.route('/updatePassword', methods = ["POST", "GET"])
def updatePassword():
    if session.get('user'):
        userId = session.get('user')
        op = request.form.get('oldPassword')
        np = request.form.get('newPassword')
        cp = request.form.get('confirmPassword')
        submit = request.form.get('submit')
        
        opM = (hashlib.md5(op.encode())).hexdigest()
        
        
        x = ['', '', '']
        y = x
        
        opQuery = database.select("SELECT * FROM user WHERE user_id='%s' && password='%s'" % (userId, opM))
        if len(opQuery) == 0 :
            x[0] = 'old password is wrong'
        if np == None or np == "" :
            np = ""
            x[1] = 'please enter a password'
        elif not re.fullmatch(r'^(?=.*?[A-Z])(?=.*?[a-z])(?=.*?[0-9])(?=.*?[#?!@$%^&*-]).{6,}$', np) :
            x[1] = 'read the note below'
        else : 
            if np == cp :
                x[2] = ''
            else :
                x[2] = 'enter the password again' 
        for val in x :
           if val == '' :
               continue
           else :
               return x
        if submit == 'true' :
            password = (hashlib.md5(np.encode())).hexdigest()
            q = "UPDATE user SET password='%s' WHERE user_id='%s'" % (password, userId)
            result = database.insert(q)
            return 'success'
        else : return y
    else:
        return redirect('/index')

@public.route('/sendFeedback', methods = ["POST", "GET"])
def sendFeedback():
    if(session.get('user')):
        userId = session.get('user')
        feedbackSub = request.form.get('feedbackSub')
        feedbackContent = request.form.get('feedbackContent')
        
        x = ['', '']
        if feedbackSub == '' or feedbackSub == None :
            x[0] = 'subject should not be empty'
        if feedbackContent == '' or feedbackContent == None :
            x[1] = 'feedback should not be empty'
        for val in x :
           if val != '' : return x
        database.insert("INSERT INTO feedback set user_id='%s', subject='%s', message='%s', user_type='user'" % (str(userId), feedbackSub.replace("'", "\\'"), feedbackContent.replace("'", "\\'")))
        return 'success'

@public.route('/deleteHistoryItem', methods = ["POST", "GET"])
def deleteHistoryItem():
    if(session.get('user')):
        userId = session.get('user')
        textId = request.form.get('textId')
        data = (database.select("SELECT file_name FROM text WHERE user_id='%s' && text_id='%s'" % (userId, textId)))[0]['file_name']
        os.unlink('static/uploads/' + data)
        database.delete("DELETE FROM text WHERE user_id='%s' && text_id='%s'" % (userId, textId))
        return 'success'
    else : return redirect('/index')

@public.route('/deletePost', methods = ["POST", "GET"])
def deletePost():
    if(session.get('user')):
        userId = session.get('user')
        postId = request.form.get('postId')
        
        database.delete("DELETE FROM post WHERE user_id='%s' && post_id='%s'" % (userId, postId))
        return 'success'
    else : return redirect('/index')

@public.route('/getComments', methods = ["POST", "GET"])
def getComments():
    userId = session.get('user') or 0  
    postId = request.form.get('postId')
    
    data = database.select("SELECT comment.*, user.* FROM comment JOIN user ON comment.user_id = user.user_id WHERE comment.post_id = '%s'" % (postId))
    return [data, userId]
    
@public.route('/addPostComment', methods = ["POST", "GET"])
def addPostComment():
    if(session.get('user')):
        postId = request.form.get('postId')
        userId = session.get('user')
        commentContent = request.form.get('commentContent')
        
        data = database.insert("INSERT INTO comment SET post_id='%s', user_id='%s', text='%s'" % (postId, userId, commentContent.replace("'", "\\'")))
        return 'success'
    else : return redirect('/login')
    
@public.route('/deleteComment', methods = ["POST", "GET"])
def deleteComment():
    if(session.get('user')):
        commentId = request.form.get('commentId')
        userId = session.get('user')
        print(commentId)
        
        result = database.delete("DELETE FROM comment WHERE comment_id='%s'" % (commentId))
        return json.dumps(result)
    else : return redirect('/login')

UPLOAD_FOLDER = '/static/uploads/'
ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg', 'gif'}
user=Blueprint('user',__name__)

@public.route('/ocrCore', methods=['GET', 'POST'])
def upload_page():
    if request.method == 'POST':
        # check if the post request has the file part
        if 'file' not in request.files:
            return "no file selected"
        file = request.files.get('file')

        # if user does not select file, browser also
        # submit a empty part without filename
        if file.filename == '':
            return "no file name"
        # check if the file extension is allowed
        if not allowed_file(file.filename):
            return "invalid file type"
        # save the file
        lang = request.form.to_dict()
        
        # print(lang)

        filename = secure_filename(file.filename) # assuming you have imported the `secure_filename` function from the appropriate module
        unique_id = str(uuid.uuid4())
        file_ext = os.path.splitext(filename)[1]
        new_filename = unique_id + file_ext
        file.save(os.path.join(os.getcwd() + UPLOAD_FOLDER, new_filename))
        # print(text)
        text = ocr_core(file, lang['language'])
        if(lang['model'] == 'tesseract'):
            text = text.replace("'", "\\'")
        elif(lang['model'] == 'handwritting' and lang['language'] == 'eng'):
            image_path = os.path.join(os.getcwd() + UPLOAD_FOLDER, new_filename)
            text = image_text(image_path)
        else:   
            def clean_and_escape_text(raw_text):
                # Remove timestamps like "9:55 / 17:48"
                cleaned = re.sub(r'\d{1,2}:\d{2}\s*/\s*\d{1,2}:\d{2}', '', raw_text)

                # Remove unwanted symbols and fragments (like ¥, and stray capital letters)
                cleaned = re.sub(r'[^a-zA-Z0-9\s.,&/-]+', '', cleaned)
                cleaned = re.sub(r'\b[A-Z]{2,}\b', '', cleaned)

                # Split into lines, strip whitespace, and remove empty lines
                lines = [line.strip() for line in cleaned.splitlines() if line.strip()]

                # Remove lines with non-English letters (after cleaning)
                lines = [line for line in lines if re.match(r'^[a-zA-Z0-9\s.,&/-]+$', line)]

                # Join lines with a separator like newline or bullet
                formatted = '\n'.join(f"- {line}" for line in lines)
                formatted = formatted.replace("'", "\\'")
                formatted = formatted.replace("`", "\\`")
                formatted = formatted.replace('"', '\\"')
                formatted = formatted.replace("’", "'")
                formatted = formatted.replace("“", '"')
                formatted = formatted.replace("”", '"')
                formatted = formatted.replace("‘", "'")
                formatted = formatted.replace("–", "-")
                formatted = formatted.replace("—", "-")
                formatted = formatted.replace("•", "-")
                formatted = formatted.replace("…", "...")

                return formatted
            text = clean_and_escape_text(text)
            if(lang['language'] != 'eng'):
                text = ""

        result = 0
        if(session.get('user')):
            userId = session.get('user')
            result = database.insert("INSERT INTO text SET user_id='"+ str(userId) +"', text='"+ text +"', new_text='"+ text +"', language='"+ lang['language'] +"', file_name='"+ new_filename +"'")   
        return [text, result]
    elif request.method == 'GET':
        return "get method is called"

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@public.route('/fileGiven', methods = ["POST", "GET"])
def fileGiven() :
    if(session.get('user')) :
        text_id = request.form.get('id')
        database.update("UPDATE text SET file_given= NOT file_given WHERE text_id='%s'" % (text_id))
        val = database.select("SELECT file_given from text WHERE text_id='%s'" % (text_id))
        return str(val[0]['file_given'])
    else : return redirect('/index')

@public.route('/sharePost', methods = ["POST", "GET"])
def sharePost() : 
    if(session.get('user')) :
        text = request.form.get('text')
        session['post'] = text
        return 'success'
    else : return redirect('/index')

@public.route('/adminLogin', methods = ['POST', 'GET'])
def adminLogin():
    if request.method == 'POST':
        x = ['', '']
        username = request.form.get('username')
        password = request.form.get('password')
        if username == None or username == "":
            x[0] = "enter the username"
            return x
        selectUserAndPasswordQuery = "SELECT id, username, password FROM admin WHERE username='"+ username +"'"
        result = database.select(selectUserAndPasswordQuery)
        if len(result) > 0 :
            if password == None or password == "" :
                x[1] = "enter the password"
                return x
            # password = (hashlib.md5(password.encode())).hexdigest()
            if result[0]['password'] == password :
                session['admin'] = result[0]['id']
                return 'success'  
            else :
                x[1] = 'wrong password'
                return x
        else : 
            x[0] = 'invalid username'
            return x
    return render_template('adminLogin.html')

@public.route('/theme/<mode>')
def theme(mode):
    session['theme'] = mode
    return 'success'

@public.route('/pdf', methods=['POST', 'GET'])
def pdf():
    data = request.form.get('data')
     # Create FPDF object
    pdf = FPDF()

    # Add a page
    pdf.add_page()

    # Set font and size
    pdf.set_font('Times', '', 10)

    lines = data.split('\n')

    # Loop through the lines and add them to the PDF
    for line in lines:
        updatedData = line.replace('\u2014', '-').replace('\u2019', "'")
        pdf.cell(80, 10, updatedData, ln=True)
    
    # Get the PDF binary data
    pdf_data = pdf.output(dest='S').encode('latin-1')

    # Set the content-type and headers
    response = make_response(pdf_data)
    response.headers.set('Content-Type', 'application/pdf')
    response.headers.set('Content-Disposition', 'attachment', filename='unknown.pdf')

    return response


@public.route('/chat', methods=['POST', 'GET'])
def chatPage():
    try:
        userData = database.select("SELECT * FROM user")
        message = request.args.get('message', '')  # Get the message from the query parameter
        print(f"Received message: {message}")  # Debugging: Log the message
        if session.get('user'):
            return render_template('chat.html', userData=userData, userLoginStatus=True, initialMessage=message)
        return render_template('chat.html', userData=userData, userLoginStatus=False, initialMessage=message)
    except Exception as e:
        print(f"Error in /chat route: {e}")  # Debugging: Log the error
        return "Something went wrong", 500


@public.route('/chatCore', methods=['POST', 'GET'])
def chat_core():
    try:
        # Get data from FormData
        user = request.form.to_dict()
        user_message = user.get("message")

        if not user_message:
            return jsonify({"reply": "❌ No message provided."}), 400

        # reply = rag(user_message)
        # if(reply != "No relevant information found in the knowledge base."):
        #     return jsonify({"reply": reply})
        
        reply = chat(user_message)
        # print(reply)
        return jsonify({"reply": reply})

    except Exception as e:
        # print("Gemini API Error:", e)
        return jsonify({"reply": f"❌ Error while getting response from Server: {e}"}), 500