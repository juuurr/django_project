from django.urls import path
from . import views


app_name = 'blog_app' #blog_app:blog -> localhost:8000/blog/post-list를 절대경로로 가리키게 됨
urlpatterns = [
    # blog 앱 내부의 경로를 지정할 부분
    # path('', views.index), #localhost:8000/blog경로, 경로를 호출하면 실행할 함수의 위치
    path('post-list', views.PostList.as_view(paginate_by=6), name='post_list'),
    path('', views.about_me, name ='about_me'),
    path('<int:pk>/', views.PostDetail.as_view()), #<자료형:필드명>
    path('create-post/', views.PostCreate.as_view(), name = "create"),

    # 글 수정과 글 작성(update와 create의 차이점 - update는 이미 있는 글을 수정하므로 글 번호가 필요함)
    path('edit-post/<int:pk>', views.PostUpdate.as_view(), name = 'update'),
    path('delete-post/<int:pk>', views.PostDelete.as_view(), name = 'delete'),

    path('user-delte', views.user_delete, name = 'user_delete'),

    #같은 tag를 가진 글끼리 게시판에 보여주깅
    path('tag/<str:slug>', views.tag_posts, name = "tag"), #<자료형:필드명>

    #댓글 조회 -> post-detail.html 안에서 동작

    #댓글 작성 <int:pk>는 글의 번호
    path('<int:pk>/create-comment', views.create_comment, name = "create_comment"),

    #댓글 수정 <int:pk>는 댓글의 번호
    path('update-comment/<int:pk>', views.CommentUpdate .as_view(), name = "update_comment"),
    #댓글 삭제
    path('delete-comment/<int:pk>', views.delete_comment, name = "delete_comment"),

    #검색을 위한 주소
    path('fsearch/<str:q>/', views.PostSearch.as_view(), name = 'post_search'),
]