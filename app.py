from flask import *
import jwt
import datetime
import pytz
import hashlib
from pymongo import MongoClient
import math
import os
from bson.objectid import ObjectId
from jwt.exceptions import ExpiredSignatureError

client = MongoClient('mongodb+srv://sparta:jungle@cluster0.sfuhxqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbjungle

app = Flask(__name__)
app.secret_key = os.urandom(24)
SECRET_KEY = 'JUNGLE'

print('jwt version : ', jwt.__version__)

@app.route('/', methods=['GET'])
def index():
    token_receive = request.cookies.get('access_token')

    page = int(request.args.get('page', 1))
    limit = 6
    offset = (page - 1) * limit
    posts = list(db.posts.find({}).sort({'regist_date':-1}).skip(offset).limit(limit))
    
    toptitle = get_best_post()

    for post in posts:
        post['_id'] = str(post['_id'])
    tot_count = list(db.posts.find({},{'_id':False}))
    last_page_num = math.ceil(len(tot_count) / limit)
    
    if last_page_num == 0:
        last_page_num = 1
    
    if token_receive is not None:
        try:
            payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
            user_info = db.users.find_one({'id':payload['id']})
            id = user_info['id']
            session["id"] = str(id)
            return render_template("index.html", id = user_info['id'], posts=posts, page=page, zip=zip, last = last_page_num, toptitle=toptitle)
        except jwt.ExpiredSignatureError:
            return render_template('index.html', msg = '로그인 시간이 만료되었습니다.', posts=posts, page=page, zip=zip, last = last_page_num, toptitle=toptitle)
    else:
        return render_template("index.html", posts=posts, page=page, zip=zip, last = last_page_num, toptitle=toptitle)
    

@app.route('/signUp', methods=['POST'])
def signUp():
    id = request.form['userId']
    pw = request.form['userPw']

    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()

    info = {'id':id, 'pw':pw_hash}

    all_id = list(db.users.find({}, {'id':1, '_id':False}))

    all_id_values = [item['id'] for item in all_id]

    if id in all_id_values:
        return jsonify({'result':'fail', 'msg':'동일한 아이디가 존재합니다'})
    else:
        db.users.insert_one(info)
        return jsonify({'result':'success'})


@app.route('/login', methods=['POST'])
def login():
    id = request.form['id']
    pw = request.form['pw']

    pw_hash = hashlib.sha256(pw.encode('utf-8')).hexdigest()

    find_user = db.users.find_one({'id':id, 'pw':pw_hash})

    if find_user is not None:
        access_payload = {
            'id': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=3)
        }
        refresh_payload = {
            'id': id,
            'exp': datetime.datetime.utcnow() + datetime.timedelta(hours=24)
        }

        access_token = jwt.encode(access_payload, SECRET_KEY, algorithm='HS256')
        refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm='HS256')

        if type(access_token) == bytes:
            access_token = access_token.decode('utf-8')
        return jsonify({'result':'success', 'access_token':access_token, 'refresh_token': refresh_token})
    else:
        return jsonify({'result':'fail', 'msg':'아이디/비밀번호가 일치하지 않습니다.'})

@app.route('/post', methods=['GET'])
def post():
    token_receive = request.cookies.get('access_token')

    pid = request.args.get('pid')
    result = db.posts.find_one({'_id':ObjectId(pid)})
    likes = db.likes.count_documents({'post_id': pid})
    likes = likes if likes == True else 0
    if token_receive is not None:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'id':payload['id']})
        id = user_info['id']
        mylike = db.likes.count_documents({'post_id': pid, "user_id": id})
        session["id"] = str(id)
        try:
            return render_template("post.html", pid=pid, title=result['title'], writer_id=result['id'], content=result['content'], time=result['regist_date'], id=user_info['id'], likes=likes, mylike=mylike)
        except jwt.ExpiredSignatureError:
            return render_template("post.html", title=result['title'], writer_id=result['id'], content=result['content'], time=result['regist_date'], pid=pid, msg="로그인 시간이 만료되었습니다.", likes=likes, mylike=mylike)
    else:
        return render_template("post.html", title=result['title'], writer_id=result['id'], content=result['content'], time=result['regist_date'], pid=pid, likes=likes, mylike=False)

@app.route('/delete', methods=['POST'])
def delete_post():
    pid = request.form['pid_give']
    db.posts.delete_one({'_id':ObjectId(pid)})
    db.likes.delete_many({'post_id': ObjectId(pid)})
    return jsonify({'result':'success'})

@app.route('/create', methods=['POST'])
def make_post():
    title = request.form['title_give']
    content = request.form['content_give']
    id = session['id']
    time = get_current_datetime()
    information = {'title': title, 'content': content, 'id': id, 'regist_date': time}
    db.posts.insert_one(information)
    return redirect(url_for('index'))


@app.route('/create', methods=['GET'])
def create():
    name = session['id']
    return render_template("create.html", id=name)


@app.route('/toggleLike', methods=['POST'])
def toggle_like():
    userId = request.form['userId']
    postId = request.form['pid']

    mylike = db.likes.find_one({'post_id': postId, 'user_id': userId})
    # 좋아요 상태 확인하고 토글
    if mylike:
        db.likes.delete_one({'post_id': postId, 'user_id': userId})
        mylike = False
    else: 
        db.likes.insert_one({'post_id': postId, 'user_id': userId})
        mylike = True

    return jsonify({'result': 'success', 'mylike': mylike})

@app.route('/getData', methods=['GET'])
def getData():
    title = request.args.get('title')
    id = request.args.get('id')
    pid = request.args.get('pid')
    object_pid = ObjectId(pid)
    content = db.posts.find_one({'_id':object_pid})['content']
    
    return render_template("update.html", title = title, content = content, id = id, pid = pid)

@app.route('/update', methods=['POST'])
def update():
    pid = ObjectId(request.form['pid'])
    title = request.form['title_give']
    content = request.form['content_give']
 
    db.posts.update_one({'_id':pid}, {'$set':{'title':title, 'content':content}})
    return redirect(url_for('index'))


@app.errorhandler(ExpiredSignatureError)
def unauthorized(error):
    url = request.url
    refresh_token = request.cookies.get('refresh_token')
    user_id = verify_refresh_token(refresh_token)
    if user_id is not None:
        access_token = generate_access_token(user_id)
        redirect_url = url_for('index')
        response = redirect(redirect_url)

    # 쿠키 설정
        response.set_cookie('access_token', access_token)
        return response

    else:
        return redirect(url_for('index'))


def verify_refresh_token(refresh_token):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=['HS256'])
        user_id = payload['id']
        return user_id
    except jwt.ExpiredSignatureError:
        # 리프레시 토큰이 만료된 경우
        return None
    except jwt.InvalidTokenError:
        # 리프레시 토큰이 유효하지 않은 경우
        return None

def generate_access_token(user_id):
    payload = {
        'id': user_id,
        'exp': datetime.datetime.utcnow() + datetime.timedelta(seconds=10)
    }
    access_token = jwt.encode(payload, SECRET_KEY, algorithm='HS256')
    return access_token

# 현재 날짜 구하는 함수
def get_current_datetime():
    current_utc_time = datetime.datetime.utcnow()

    kr_tz = pytz.timezone('Asia/Seoul')
    time = current_utc_time.replace(tzinfo=pytz.utc).astimezone(kr_tz)
    time = time.strftime('%Y-%m-%d %H:%M:%S')

    return time

# 가장 인기있는 게시글 찾는 함수
def get_best_post():
    time = get_current_datetime().split()[0]
    group = db.likes.aggregate([ 
        {"$group":{"_id":"$post_id", "count":{"$sum":1}}}
        ])
    maxlike = ('',-1)
    for g in list(group):
        post1 = db.posts.find_one({"_id":ObjectId(g['_id'])})
        if post1 is not None:
            if post1['regist_date'].split()[0] == time:
                if g['count'] > maxlike[1]:
                    maxlike = (g['_id'], g['count'])
                elif g['count'] == maxlike[1]:
                    post2 = db.posts.find_one({"_id":ObjectId(maxlike[0])})
                    if post1['regist_date'] > post2['regist_date']:
                        maxlike = (g['_id'], g['count'])
            else:
                continue
    if maxlike[0]:
        result = db.posts.find_one({"_id":ObjectId(maxlike[0])})
    else:
        result = False

    print(result)
    return result 

if __name__ == '__main__':
    app.run('0.0.0.0',port=5011,debug=True)
