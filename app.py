from flask import *
import jwt
import datetime
import hashlib
from pymongo import MongoClient
import math

client = MongoClient('mongodb+srv://sparta:jungle@cluster0.sfuhxqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbjungle

app = Flask(__name__)

SECRET_KEY = 'JUNGLE'

@app.route('/', methods=['GET'])
def index():
    token_receive = request.cookies.get('mytoken')

    page = int(request.args.get('page', 1))
    print(page)
    limit = 6
    offset = (page - 1) * limit
    posts = list(db.posts.find({},{'_id':False}).skip(offset).limit(limit))
    tot_count = list(db.posts.find({},{'_id':False}))
    last_page_num = math.ceil(len(tot_count) / limit)
    print(posts)

    if token_receive is not None:
        payload = jwt.decode(token_receive, SECRET_KEY, algorithms=['HS256'])
        user_info = db.users.find_one({'id':payload['id']})
        return render_template("index.html", id = user_info['id'], posts=posts, page=page, zip=zip, last = last_page_num)
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

        return jsonify({'result':'success', 'token':token})
    else:
        return jsonify({'result':'fail', 'msg':'아이디/비밀번호가 일치하지 않습니다.'})



if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)
