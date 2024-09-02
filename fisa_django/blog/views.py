from typing import Any
from django.db.models.query import QuerySet, Q
from django.forms.models import BaseModelForm
from django.http import HttpRequest, HttpResponse
from django.shortcuts import render, redirect
from .models import Post, Tag, Comment
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.utils.text import slugify

from .forms import CommentForm
# 회원탈퇴
from django.views.decorators.http import require_POST #POST 방식으로만 접근해야하는 함수 앞에 적어줌
from django.contrib.auth import logout as auth_logout #logout을 담당하는 함수
from django.contrib.auth import authenticate, login # authenticate : 인가, login : 인증 담당
from django.contrib.auth.decorators import login_required #인증을 확인해서 로그인 상태에서만 접근할 수 있게 허가하는 데코레이터
from django.core.exceptions import PermissionDenied #인가 - 퀀한이 없으면 예외 발생
from django.contrib import messages #예외나 상황에 대한 메시지 처리 
from django.contrib.auth.mixins import LoginRequiredMixin

#Mixin이라는 부가 기능들을 확인하기 위해 다중 상속으로 주 기능을 확장하는 별도의 클래스
#주기능을 가진 클래스 앞에 작성

#User의 정보를 필드로 달아서 보내면 변조 가능하기 떄문에 view에서 처리함
class PostCreate(LoginRequiredMixin, CreateView) :
    model = Post
    fields = ["title", "content", "head_image", "file_upload"]

    # CreateView가 내장한 함수 - 오버라이딩
    # tag는 참조관계이므로 Tag 테이블에 등록된 태그만 쓸 수 있는 상황
    # 임의로 방문자가 form에 Tag를 달아서 보내도록 form_valid()에 결과를
    # 저장된 포스트로 돌아오도록
    def form_valid(self, form):
        current_user = self.request.user
        if current_user.is_authenticated and (current_user.is_active):
            form.instance.author = current_user
            response = super(PostCreate, self).form_valid(form)
            tags_str = self.request.POST.get('tags_str')
            if tags_str:
                tags_str = tags_str.strip()

                tags_str = tags_str.replace(',', ';')
                tags_list = tags_str.split(';')

                for t in tags_list:
                    t = t.strip()
                    tag, is_tag_created = Tag.objects.get_or_create(tag_name=t)
                    if is_tag_created:
                        tag.slug = slugify(t, allow_unicode=True)
                        tag.save()
                    self.object.tag.add(tag)
            return response
        else:
            return redirect('/blog/')

class PostUpdate(LoginRequiredMixin, UpdateView) :
    model = Post
    fields = ["title", "content", "head_image", "file_upload"]

    # 로그인한 상태에서 작성자(request.user)가 글의 author와 일치하는지 확인
    #방문자가 GET/POST 요청 등을 동작 수행 전에 가로채서 확인하는 기능
    def dispatch(self, request, *args, **kwargs): # 방문자가 GET으로 요청했는데 POST로 요청했는지 확인하는 기능
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(PostUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied #403에러
        
    # author 필드는 당연히 이전에 글을 생성한 작성자로 채워져있고, 
    # LoginRequiredMixin으로 로그인한 유저 확인하므로 form_valid는 오버라이딩하지 않음
    # 태그에 여러개 보내면 겹치지 않는 것만 새로 성성하는 기능은 필요하므로 get_context_data를 오버라이딩   
    #이미 있는 글을 불러와서, 그 글을 바탕으로 원본을 수정한 내용을 변경
    def get_context_data(self, **kwargs):
        context = super(PostUpdate, self).get_context_data()
        if self.object.tag.exists():
            tags_str_list = list()
            for t in self.object.tag.all():
                tags_str_list.append(t.tag_name)
            context['tags_str_default'] = '; '.join(tags_str_list)

        return context
    
    # 포스트에 태그를 추가하려면 이미 데이터베이스에 저장된 pk를 부여받아서 수정해야 함, 
    # 그래서 form_valid()를 통해 결과를 response 변수에 임시 담아두고
    # 서로 저장된 포스트를 self.object로 저장함.
    def form_valid(self, form):
        response = super(PostUpdate, self).form_valid(form)
        self.object.tag.clear()

        tags_str = self.request.POST.get('tags_str')
        if tags_str:
            tags_str = tags_str.strip()
            tags_str = tags_str.replace(',', ';')
            tags_list = tags_str.split(';')

            for t in tags_list:
                t = t.strip()
                tag, is_tag_created = Tag.objects.get_or_create(tag_name=t)
                if is_tag_created:
                    tag.slug = slugify(t, allow_unicode=True)
                    tag.save()
                self.object.tag.add(tag)

        return response

class PostDelete(LoginRequiredMixin, DeleteView):
    model = Post 
    success_url = '/blog/post-list'

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        if self.object.author == request.user:
            success_url = self.get_success_url()
            self.object.delete()
            return redirect(success_url)
        else:
            raise PermissionDenied
class PostList(ListView):   # post_list.html, post-list
    model = Post 
    # template_name = 'blog/index.html' 
    ordering = '-pk' 
    context_object_name = 'post_list'

class PostSearch(PostList):
    paginate_by = None #상속받을때 pagination 사용하지 않겠당
    def get_queryset(self):
        q = self.kwargs['q'] # q = 'new'
        #title에 있거나, content에 있거나, tag에 있거나
        post_list = Post.objects.filter(Q(title__contains=q) | Q(content__contains=q) | Q(tag__tag_name__contains=q)).select_related('author')
        return post_list

def index(request): # 함수를 만들고, 그 함수를 도메인 주소 뒤에 달아서 호출하는 구조
    posts = Post.objects.all()
    return render(
        request,
        'blog/index.html', {
            'posts':posts, 'my_list': ["apple", "banana", "cherry"], 'my_text': "첫번째 줄 \n 두번째 줄", 'content' : '<img src="data/jjangu.jpg" / >'
        }
    )# 없는 index.html을 호출하고 있음

def about_me(request): # 함수를 만들고, 그 함수를 도메인 주소 뒤에 달아서 호출하는 구조
    return render(
        request,
        'blog/about_me.html'
    )

class PostDetail(DetailView): # 함수를 만들고, 그 함수를 도메인 주소 뒤에 달아서 호출하는 구조
    model = Post 

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["now"] = '임의로 작성한 새로운 변수'
        context["comment_form"] = CommentForm
        print(context['now'])
        return context

    
def user_delete(request):
    #로그인 상태 확인
    if request.user.is_authenticated:
        #user.delete() 호출
        request.user.delete()
        
        #로그아웃
        auth_logout(request) # 세션을 지워줌

        #원래 페이지로 로그인 안된 상태로 원상 복귀
        return redirect('blog_app:about_me')

#태그(slug)가 일치하는 글을 함께 출력
#path('tag/<str:slug>', views.tag_posts, name = "tag"), #<자료형:필드명>
def tag_posts(request, slug):
    #tag가 없는 경우
    if slug == "no-tag":
        posts = Post.objects.filter(tag = None)
    #tag가 있는 경우
    else :
        tag = Tag.objects.get(slug=slug) #tag를 포함한 Object를 추려냄
        # posts = Post.objects.filter(tag=tag)
        posts = Post.objects.filter(tag=tag).select_related('author')# 쿼리 최적화를 위해서  foreignKey나 1:1관계로 연결된 테이블 데이터를 한번에 가져옴
        #한번에 데이터를 저장해놓고 필요할 때 재사용
    return render(request, 'blog/post_list.html', {'post_list':posts}) #템플릿 재사용

#댓글 작성
def create_comment(request, pk):
    #GET/POST 서로 다른 결과 return
    #로그인 상태 확인
    if request.user.is_authenticated: #로그인한 경우
        post = Post.objects.get(pk=pk)

        if request.method == 'POST':
            comment_form = CommentForm(request.POST) #작성한 content
            if comment_form.is_valid():
                comment = comment_form.save(commit=False) #임시저장, 객체는 만들었지만 아직 DB에 저장x
                comment.post = post
                comment.author = request.user
                comment.save()
                return redirect(comment.get_absolute_url())
        else: #post방식으로 들어오지 않은 경우
            return redirect(post.get_absolute_url())
    else: #로그인을 안한 경우
        return PermissionDenied
    #댓글 작성 <int:pk>는 글의 번호
    #path('<int:pk>/create-comment', views.create_comment, name = "create_comment"),

#댓글 수정 <int:pk>는 댓글의 번호
class CommentUpdate(LoginRequiredMixin, UpdateView): #updateview를 상속받아서 씀
    model = Comment
    form_class = CommentForm
    def dispatch(self, request, *args, **kwargs): # 방문자가 GET으로 요청했는데 POST로 요청했는지 확인하는 기능
        if request.user.is_authenticated and request.user == self.get_object().author:
            return super(CommentUpdate, self).dispatch(request, *args, **kwargs)
        else:
            raise PermissionDenied #403에러

    #원래의 댓글을 가지고 해당 경로에 가야함

def delete_comment(request, pk):
    comment = Comment.objects.get(pk=pk) #comment 객체를 가져옴
    post = comment.post #comment의 번호를 가져옴

    #로그인 된 상태이고 comment.author이면
    if request.user.is_authenticated and request.user == comment.author:
        comment.delete()
        return redirect(post.get_absolute_url())
    else:
        raise PermissionDenied



#class CommentDelete(request, DeleteView): #deleteView를 상속받아서 씀
#    model = Comment
#    success_url = '/blog/'

    #로그인 된 상태이고, comment.author이면
    