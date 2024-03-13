from flask import *
import jwt
import datetime
import pytz
import hashlib
from pymongo import MongoClient
import math
import os
from bson.objectid import ObjectId

client = MongoClient('mongodb+srv://sparta:jungle@cluster0.sfuhxqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbjungle

app = Flask(__name__)
app.secret_key = os.urandom(24)
SECRET_KEY = 'JUNGLE'

@app.route('/', methods=['GET'])
def index():
    token_receive = request.cookies.get('mytoken')

    page = int(request.args.get('page', 1))
    print(page)
    limit = 6
    offset = (page - 1) * limit
    posts = list(db.posts.find({}).skip(offset).limit(limit))
    for post in posts:
        post['_id'] = str(post['_id'])
    tot_count = list(db.posts.find({},{'_id':False}))
    last_page_num = math.ceil(len(tot_count) / limit)
    print(posts)
    
    if token_receive is not None:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            user_info = db.users.find_one({'id':payload['id']})
            id = user_info['id']
            session["userid"] = str(id)
            return render_template("index.html", id = user_info['id'], posts=posts, page=page, zip=zip, last = last_page_num)
        except jwt.ExpiredSignatureError:
            return render_template('index.html', msg = '로그인 시간이 만료되었습니다.', posts=posts, page=page, zip=zip, last = last_page_num)
    else:
        return render_template("index.html", posts=posts, page=page, zip=zip, last = last_page_num)
    
    
    

@app.route('/signUp', methods=['POST'])
def signUp():
    id = request.form['user_id']
    pw = request.form['user_pw']
    name = request.form['user_name']

    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()

    info = {'id':id, 'pw':pw_hash, 'name':name}
    
    db.users.insert_one(info)
    return redirect(url_for('index'))


@app.route('/idCheck', methods=['POST'])
def idCheck():
   userId = request.form['userId']
   all_id = list(db.users.find({}, {'id':1, '_id':False}))

   all_id_values = [item['id'] for item in all_id]

   if userId in all_id_values:
      return '0'
   else:
      return '1'


@app.route('/login', methods=['POST'])
def login():
    id = request.form['id']
    pw = request.form['pw']

    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()

    find_user = db.users.find_one({'id':id, 'pw':pw_hash})

    if find_user is not None:
        payload = {
            'id': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(minutes=60)
        }
        token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
        if type(token) == bytes:
            token = token.decode('utf-8')
        return jsonify({'result':'success', 'token':token})
    else:
        return jsonify({'result':'fail', 'msg':'아이디/비밀번호가 일치하지 않습니다.'})


@app.route('/post', methods=['GET'])
def post():
    pid = request.args.get('pid')
    print(pid)
    result = db.posts.find_one({'_id':ObjectId(pid)})
    print(result)

    return render_template("post.html", title=result['title'], id=result['id'], content=result['content'], time=result['regist_date'])

@app.route('/create', methods=['POST'])
def make_post():
    title = request.form['title_give']
    content = request.form['content_give']
    id = session['userid']
    time = get_current_datetime()
    information = {'title': title, 'content': content, 'id': id, 'regist_date': time}
    print(title, content, id)
    db.posts.insert_one(information)
    return redirect(url_for('index'))


@app.route('/create', methods=['GET'])
def create():
    id = session['userid']
    return render_template("create.html", id=id)


# 현재 날짜 구하는 함수
def get_current_datetime():
    current_utc_time = datetime.datetime.utcnow()

    kr_tz = pytz.timezone('Asia/Seoul')
    time = current_utc_time.replace(tzinfo=pytz.utc).astimezone(kr_tz)
    time = time.strftime('%Y-%m-%d %H:%M:%S')

    return time

if __name__ == '__main__':
    app.run('0.0.0.0',port=5011,debug=True)
