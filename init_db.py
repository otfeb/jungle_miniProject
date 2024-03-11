import requests
from bs4 import BeautifulSoup
from pymongo import MongoClient

client = MongoClient('mongodb+srv://sparta:<password>@cluster0.sfuhxqa.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0')
db = client.dbjungle

    
# 타겟 URL을 읽어서 HTML를 받아오고,
headers = {'User-Agent' : 'Mozilla/5.0 (Windows NT 10pip .0; Win64; x64)AppleWebKit/537.36 (KHTML, like Gecko) Chrome/73.0.3683.86 Safari/537.36'}
url = 'https://news.naver.com/section/105'
data = requests.get(url,headers=headers)

# HTML을 BeautifulSoup이라는 라이브러리를 활용해 검색하기 용이한 상태로 만듦
# soup이라는 변수에 "파싱 용이해진 html"이 담긴 상태가 됨
# 이제 코딩을 통해 필요한 부분을 추출하면 된다.

soup = BeautifulSoup(data.text, 'html.parser')
books = soup.select('#_SECTION_HEADLINE_LIST_4i8lc > li')
db.books.drop()
print(data)
for i in books:
    print(i)

print("mission complete!")