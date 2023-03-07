import math
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from .form import UserForm
from myapp02.models import Board, Comment
from django.http.response import JsonResponse, HttpResponse
import urllib.parse
from django.db.models import Q
from django.core.paginator import Paginator


# Create your views here.

UPLOAD_DIR = 'C:/DjangoWork/myProject02/upload02'

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
        
    board = Board(writer = request.POST['writer'],
                title = request.POST['title'],
                content = request.POST['content'],
                filename = fname,
                filesize = fsize
		)
    board.save()
    return redirect('/list/')

def list_page(request):
    page = request.GET.get('page',1)    
    word = request.GET.get('word','')

    boardCount = Board.objects.filter(Q(writer__contains=word)|
                                      Q(title__contains=word)|
                                      Q(content__contains=word)).count()
    
    boardList = Board.objects.filter(Q(writer__contains=word)|
                                     Q(title__contains=word)|
                                     Q(content__contains=word)).order_by('-id')
    
    pageSize = 5
    #페이징 처리
    paginator = Paginator(boardList,pageSize)
    page_obj = paginator.get_page(page)
    # print('page_obj : ', page_obj)

    context={'page_list' : page_obj,
             'word' : word,
             'boardCount':boardCount,
             }
    return render(request, 'board/list_page.html', context)


def list(request):
    page = request.GET.get('page',1)    
    field = request.GET.get('field','title')
    word = request.GET.get('word','')
    # count
    if field == 'all':
        boardCount = Board.objects.filter(Q(writer__contains=word)|
                                         Q(title__contains=word)|
                                         Q(content__contains=word)).count()
    elif field == 'writer':
        boardCount = Board.objects.filter(Q(writer__contains=word)).count()
    elif field == 'title':
        boardCount = Board.objects.filter(Q(title__contains=word)).count()
    elif field == 'content':
        boardCount = Board.objects.filter(Q(content__contains=word)).count()
    # else :
    #     boardCount = Board.objects.all().count() #"if field == 'all':"이 있으므로 없어도 잘 돌아감.

    pageSize = 5
    blockPage = 3
    currentPage = int(page)
    totPage = math.ceil(boardCount/pageSize)
    startPage = math.floor((currentPage-1)/blockPage)*blockPage+1
    endPage = startPage + blockPage -1 
    if endPage > totPage:
        endPage = totPage

    start = (currentPage-1)*pageSize

    #내용
    if field == 'all':
        boardList = Board.objects.filter(Q(writer__contains=word)|
                                         Q(title__contains=word)|
                                         Q(content__contains=word)).order_by('-id')[start:start+pageSize]
    elif field == 'writer':
        boardList = Board.objects.filter(Q(writer__contains=word)).order_by('-id')[start:start+pageSize]
    elif field == 'title':
        boardList = Board.objects.filter(Q(title__contains=word)).order_by('-id')[start:start+pageSize]
    elif field == 'content':
        boardList = Board.objects.filter(Q(content__contains=word)).order_by('-id')[start:start+pageSize]
    # else :
    #     boardList = Board.objects.all().order_by('-idx') #"if field == 'all':"이 있으므로 없어도 잘 돌아감. #[start:start+pageSize] 슬라이싱 없이 잘 돌아감.

    # boardList = Board.objects.all().order_by('-id')[start:start+pageSize]
    # range(startPage, endPage+1)
    context = {'boardList':boardList,
               'boardCount':boardCount,
               'blockPage':blockPage,
               'currentPage':currentPage,
               'totPage':totPage,
               'startPage':startPage,
               'endPage':endPage,
               'range':range(startPage, endPage+1),
               'field':field,
               'word':word,
               }
    return render(request, 'board/list.html', context)

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

def detail(request,board_id):
    board = Board.objects.get(id=board_id)
    board.hit_up()  # 조회수 증가
    board.save()
    return render(request, 'board/detail.html',{'board':board})

def delete(request,board_id):
    Board.objects.get(id=board_id).delete()
    return redirect('/list/')

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
                         writer = request.POST['writer'],
                         title = request.POST['title'],
                         filename = fname,
                         filesize = fsize
                         )
    update_board.save()
    return redirect('/list/')


@csrf_exempt
def comment_insert(request):
    id = request.POST['id']
    comment = Comment(board_id = id,
                      writer = 'aa',
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
            return redirect('/')
        else:
            print('signup POST un_valid')
    else:
        form = UserForm()
    return render(request,'common/signup.html',{'form':form})