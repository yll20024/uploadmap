# uploadmap
本程序为python编写，python版本3.7.2，针对常见的文件上传漏洞进行检测，shell类型为php，后续可能会增加对asp,jsp,aspx,jspx,asa,asax等类型的支持(这些在ctf中不大常见)。设计这个程序的初衷是为了方便做ctf，解放双手。。。

目前适用漏洞：
1.无限制
2.前端js检查
3.MIME检查
4.扩展名黑名单（大小写、不常见可解析扩展名）
5.htaccess、user.ini重写
6.<?检查（html形式）
7.双写绕过
8.点绕过（1.php.）
9.空格绕过（1.php ）
10.点空格点绕过（1.php. .）
11.冒号绕过（1.php:1.jpg）
12.::$DATA绕过
13.文件头检查
14.nginx、apache解析漏洞
15.以上漏洞的组合（比如前端js检查+MIME检查+<?检查+扩展名黑名单+文件头检查）

程序的使用方法：
目前暂时采用直接修改变量的方式传参
参数列表：
requestFilePath---字符串---不可空---请求包文件路径,brup抓包,repeater->copy to file
responseFilePath---字符串---不可空---响应包文件路径,burp抓包,repeater->copy to file,用[[[[]]]]标记响应包中返回的上传文件的路径
https---逻辑型---可空---网站是否开启https,默认关闭
base_url---字符串---可空---该变量为正常文件上传成功时的完整url路径,为空时程序自动判断(http(s)://+host+port+请求头+响应包返回的url）程序判断错误时需要指定。例：上传成功后文件url：http://www.xxx.com/upload/1.jpg,此时该变量写：http://www.xxx.com/upload/[[]]
custom_Y---字符串---可空---自定义条件,在逐条验证payload时,如果返回包存在custom_Y中的一个或多个内容,则判定通过,不再验证下一条payload,条件之间可用&或|连接,但不可同时出现,不支持逻辑括号
custom_N---字符串---可空---自定义条件,在逐条验证payload时,如果返回包不存在custom_N中的一个或多个内容,则判定通过,不再验证下一条payload,条件之间可用&或|连接,但不可同时出现,不支持逻辑括号
**注:custom_Y和custom_N不可同时非空，&和|不可同时出现，不支持逻辑括号及其嵌套(本人能力有限,写不了那么复杂的逻辑判断....)**

**可以设置这样的自定义条件：**

custom_N="不能上传php文件&不是图片文件&文件内容不合法“
意思是响应包中不出现上面的所有内容时停止。（最常用）

custom_N="我扌your problem111|我扌your problem222|我扌your problem333“
意思是响应包中不出现上面任意一个内容时停止。

custom_Y="我扌your problem111&我扌your problem222&我扌your problem333“
意思是响应包中出现上面的所有内容时停止。

custom_Y="我扌your problem111|我扌your problem222|我扌your problem333“
意思是响应包中出现上面任意一个内容时停止。

**不能设置这样的自定义条件：**

**custom_N="con1|con2&con3“**
**custom_N="(con1|con2)&con3“**
**custom_Y="(con1&(con2|con3)|con4)&con5“**

**条件中出现的括号会当做普通字符对待**

后续开发中会增加一些payload和跟随重定向的选项（适用条件：文件上传成功后跳转到新的网页才返回上传结果）,响应包如果出现重定向,程序自动跟随地址，并取出重定向地址的文件url
总体来说程序一般，实用性一般，自己用的还比较顺手，还是有点成就感的......
