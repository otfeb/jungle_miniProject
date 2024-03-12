from flask import *
from pymongo import MongoClient
import math

client = MongoClient('mongodb+srv://sparta:jungle@cluster0.sfuhxqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbjungle

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    page = int(request.args.get('page', 1))
    print(page)
    limit = 6
    offset = (page - 1) * limit
    posts = list(db.posts.find({},{'_id':False}).skip(offset).limit(limit))
    tot_count = list(db.posts.find({},{'_id':False}))
    last_page_num = math.ceil(len(tot_count) / limit)
    print(posts)
    return render_template("index.html", posts=posts, page=page, zip=zip, last = last_page_num)

@app.route('/signUp', methods=['POST'])
def signUp():
    id = request.form['user_id']
    pw = request.form['user_pw']
    name = request.form['user_name']

    info = {'id':id, 'pw':pw, 'name':name}
    
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
   
@app.route('/post', methods=['GET'])
def post():
    return render_template("post.html")

if __name__ == '__main__':
    app.run('0.0.0.0',port=5000,debug=True)
