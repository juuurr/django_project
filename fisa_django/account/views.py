from django.shortcuts import render
from .forms import LoginForm
from django.contrib.auth import login, authenticate
from django.http import HttpResponse

# Create your views here.

def user_login(request): #주소줄로 요청을 받아서 일할거야
    # 요청의 방법 확인 POST
    if request.method == 'POST':
        #폼에서 데이터를 받아서 유효성 검사(ex. 아이디랑 비밀번호를 모두 입력했는지)
        form = LoginForm(request.POST) #데이터 받기
        if form.is_valid(): #유효성 검사
            cd = form.cleaned_data #dict 형식으로 form에서 온 데이터를 정제해주는 속성
            
            #입력받은 username, password를 DB와 일치하는지 확인
            user = authenticate(request, username=cd['username'], password=cd['password'])
            if user is not None: #입력된 값이 있으면(휴면계정이 아닌지 확인)
                if user.is_active : #휴면계정이 아닌 경우
                    login(request, user) #로그인해주세용 (최상위 함수와 동일한 함수명 사용 -> 순환참조)
                    response = HttpResponse() #입력받은 USER가 일치하면 응답 객체 생성, 결과 response를 전달

                    #쿠키
                    response.set_cookie('user', user)
                    response.set_cookie('testCookie', 'value testCookie')
                    response.set_cookie('testCookie', 'value testCookie2')

                    #세션
                    request.session['testSession'] = 'value session'

                    response.content = f"로그인 되었습니다! {request.COOKIES.get('user'), request.COOKIES.get('testCookie')} \n session: {request.session.get('testSession')}"
                    return response
                else:
                    return HttpResponse("사용 불가에용 ㅠㅠ")
        else:
            return HttpResponse("로그인 정보가 틀려유ㅠ~ㅠ") # USER가 일치하지 않으면 ; 잘못 입력하셨습니다. 
    else:
        form = LoginForm()
    return render(request, 'account/login.html', {'form':form})
        
        