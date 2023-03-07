import json
import os
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required

from django.http.response import JsonResponse, HttpResponse

from .form import UserForm
from django.db.models import Q
from django.core.paginator import Paginator
import urllib.parse

#######
from myapp03.models import Board, Comment, Forecast, Movie
from myapp03 import bigdataProcess
from myProject03.settings import TEMPLATE_DIR
from django.db.models.aggregates import Count, Avg
import pandas as pd
import folium

# Create your views here.

UPLOAD_DIR = 'C:/DjangoWork/myProject03/upload03'


# wordcloud
def wordcloud(request):
    a_path = "C:/DjangoWork/myProject03/data/"
    data = json.loads(open(a_path+'4차 산업혁명.json','r',encoding='utf-8').read())
    bigdataProcess.make_wordCloud(data)
    return render(request, 'bigdata/word.html',{"img_data":'k_wordCloud.png'})


# movie_chart2
def movie_chart2(request):
    data=[]
    bigdataProcess.movie_crawling(data)
    # print(data)
    df = pd.DataFrame(data, columns=['제목', '평점', '내용'])
    # print(df)
    # group_title = df.groupby('제목')
    # print(group_title)
    
    # 제목별 그룹화 해서 평점의 평균
    group_mean = df.groupby('제목')['평점'].mean().sort_values(ascending=False).head(10)
    # print(group_mean)
    df1 = pd.DataFrame(group_mean, columns=['평점'])
    # print(df1)
    bigdataProcess.movie_naver_chart(df1.index, df1.평점)

    return render(request, 'bigdata/movie_naver.html',{'data' : data, 'img_data' : 'movie_naver_fig.png'})



# movies
def movies(request):
    data=[]
    bigdataProcess.movies(data)

    return render(request, 'bigdata/movies.html',{'data':data})

#movie
def movie(request):
    data = []
    bigdataProcess.movie_crawling(data)
    # data 들어있는 순서 : title, point, content
    for r in data:
        movie = Movie(title=r[0],
                      point=r[1],
                      content=r[2])
        movie.save()

    return redirect('/')

def movie_chart(request):
    # movie 테이블에서 제목(title)에 해당하는 평점(point) 평균을 구하기
    data = Movie.objects.values('title').annotate(point_avg = Avg('point'))[0:10]
    # print('data query : ', data.query) # sql문 확인
    df = pd.DataFrame(data)
    bigdataProcess.movie_chart(df.title, df.point_avg)

    return render(request, 'bigdata/movie.html', {'data':data,"image_data":'movie_fig.png'})


#melon
def melon(request):
    # 순위 곡명 가수 앨범
    datas = []
    bigdataProcess.melon_crawling(datas)

    return render(request, 'bigdata/melon1.html', {'data': datas})

#map
def map(request):
    bigdataProcess.map()
    return render(request, 'bigdata/map.html')


#weather
def weather(request):
    last_date = Forecast.objects.values('tmef').order_by('-tmef')[:1]

    weather = {}
    bigdataProcess.weather_crawling(last_date, weather)
    # print(last_date.query) : SQL문 출력 
    # print('weather : ', weather)
    
    for i in weather:
        for j in weather[i]:
            dto = Forecast(city = i,
                           tmef = j[0],
                           wf = j[1],
                           tmn = j[2],
                           tmx = j[3])
            dto.save()
            
    result = Forecast.objects.filter(city='부산')
    result1 = Forecast.objects.filter(city='부산').values('wf').annotate(dcount = Count('wf')).values("dcount","wf")
    # print('result1 : ', result1.query)
    df = pd.DataFrame(result1)
    # print('df : ', df)
    image_dic = bigdataProcess.weather_make_chart(result, df.wf, df.dcount)
    # print('image_dic : ',image_dic)



    return render(request, 'bigdata/chart.html', {'image_dic' : image_dic})


#######################
def list(request):
    page = request.GET.get('page',1)    
    word = request.GET.get('word','')

    boardCount = Board.objects.filter(Q(writer__username__contains=word)|
                                      Q(title__contains=word)|
                                      Q(content__contains=word)).count()
    
    boardList = Board.objects.filter(Q(writer__username__contains=word)|
                                     Q(title__contains=word)|
                                     Q(content__contains=word)).order_by('-id')
    
    pageSize = 5
    #페이징 처리
    paginator = Paginator(boardList,pageSize)
    page_obj = paginator.get_page(page)
    # print('page_obj : ', page_obj)

    rowNo = boardCount-(int(page)-1)*pageSize

    context={'page_list' : page_obj,
             'word' : word,
             'boardCount':boardCount,
             'rowNo' : rowNo,
             }
    return render(request, 'board/list.html', context)

@login_required(login_url='/login/')
def write_form(request):
    return render(request, 'board/insert.html')

@csrf_exempt
def insert(request):
    fname = ''
    fsize = 0
    if 'file' in request.FILES:
        file = request.FILES['file']
        fname = file.name
        fsize = file.size
        fp = open('%s%s' %(UPLOAD_DIR,fname), 'wb')
        for chuck in file.chunks():
            fp.write(chuck)
        fp.close()
        
    board = Board(writer = request.user,
                title = request.POST['title'],
                content = request.POST['content'],
                filename = fname,
                filesize = fsize
		)
    board.save()
    return redirect('/list/')

def detail(request,board_id):   
    board = Board.objects.get(id=board_id)
    board.hit_up()
    board.save()
    return render(request, 'board/detail.html',{'board':board})   

@csrf_exempt
def comment_insert(request):
    id = request.POST['id']
    comment = Comment(board_id = id,
                      writer =  request.user,
                      content = request.POST['content']
                      )
    comment.save()
    return redirect('/detail/'+id)


def signup(request):
    if request.method=="POST":
        form = UserForm(request.POST)
        if form.is_valid():
            print('signup POST is_valid')
            form.save()
            username = form.cleaned_data.get('username')
            raw_password = form.cleaned_data.get('password1')
            user = authenticate(username=username, password=raw_password)
            login(request,user)
            return redirect('/')
        else:
            print('signup POST un_valid')
    else:
        form = UserForm()
    return render(request,'common/signup.html',{'form':form})






def update_form(request,board_id):
    board = Board.objects.get(id=board_id)
    return render(request, 'board/update.html',{'board':board})

@csrf_exempt
def update(request):
    id = request.POST['id']
    board = Board.objects.get(id=id)
    fname = board.filename
    fsize = board.filesize
    if 'file' in request.FILES: # file 수정
        file = request.FILES['file']
        fname = file.name
        fsize = file.size
        fp = open('%s%s' %(UPLOAD_DIR,fname), 'wb')
        for chunk in file.chunks():
            fp.write(chunk)
        fp.close()

    update_board = Board(id,
                         writer = request.user,
                         title = request.POST['title'],
                         content = request.POST['content'],
                         filename = fname,
                         filesize = fsize
                         )
    update_board.save()
    return redirect('/list/')

def delete(request,board_id):
    Board.objects.get(id=board_id).delete()
    return redirect('/list/')

def download_count(request):
    id = request.GET['id']
    board = Board.objects.get(id = id)
    board.down_up() # 다운로드 수 1 증가
    board.save()
    count = board.down # 다운로드 수
    return JsonResponse ({'id' : id, 'count' : count})

def download(request):
    id = request.GET['id']

    board = Board.objects.get(id=id)
    path = UPLOAD_DIR+board.filename
    filename = urllib.parse.quote(board.filename)
    with open(path, 'rb') as file:
        response = HttpResponse(file.read(),
                                content_type='application/octet-stream')
        response['Content-Disposition']="attachment;filename*=UTF-8''{0}".format(filename)
    return response
