from PIL import Image
import requests
import datetime
import json
from bs4 import BeautifulSoup
import re
from moviepy.editor import VideoFileClip
import random
import time
from fake_useragent import UserAgent

ua = UserAgent()


session = requests.Session()
Course_list = []
cur_course = ''
Chapter_list = []
Video_list = []
random_ua= ua.random
html = ''
username = ''
password = ''

headers = {
    'User-Agent': random_ua
}

class Video:
    def __init__(self, isComplete='', url='', kcdm='', zjdm='', bjdm='', spdm='', yhdm='', spbfsc=0.000000, spzsc='', zjmc=''):
        self.isComplete = isComplete
        self.url = url          # url                   video_info
        self.kcdm = kcdm        # kcdm                  chapter
        self.zjdm = zjdm        # zjdm                  chapter
        self.bjdm = bjdm        # bjdm                  chapter
        self.spdm = spdm        # spdm                  video_info
        self.yhdm = yhdm        # 默认为空 ""            ""
        self.spbfsc = spbfsc    # 观看时长(保留六位小数) 15s + %0.6lf
        # 视频时长              url -> get_duration_from_moviepy(url) -> time(spzsc)
        self.spzsc = spzsc
        self.zjmc = zjmc        # 章节名                chapter_info


class Course:
    def __init__(self, name, progress, param, start_time, end_time):
        self.name = name  # 课程名字
        self.progress = progress  # 学习进度
        self.param = param  # chapter id
        self.start_time = start_time  # 开始时间
        self.end_time = end_time  # 结束时间

    def display_info(self):
        print(f"课程名字: {self.name}", end="\t")
        print(f"学习进度: {self.progress}", end="\t")
        print(f"{self.start_time}", end="\t")
        print(f"{self.end_time}")


def notice():
    print("--------------------")
    print("荣优学堂 auto player")
    print("--------------------")
    print("  鸣谢： HAUST 小南 ")
    print("--------------------")
    print("项目地址：")
    print("https://github.com/AlwaysLazy21/RongYouXueTang")
    print("----------------------------------------------")
    print("author: AlwaysLazy21")
    print("--------------------")
    print("当前及支持手机号登录")


def write_log(info: str):
    current_time = datetime.datetime.now()
    with open(file='log.txt', mode='a', encoding='UTF_8')as f:
        f.write(str(current_time) + info + "\n")


def input_User_profile():
    global username, password
    username = input("请输入你的用户名：") or username
    password = input("请输入你的密码：") or password


def input_Verification_code():
    Verification_code = Image.open(fp="captchaImage.jpg")
    Verification_code.show()
    cin_Verification_code = input("请输入验证码：")
    Verification_code.close()
    return cin_Verification_code


def get_captchaImage():
    target_url = "https://www.livedu.com.cn/ispace4.0/captchaImage"
    global headers
    resp = session.get(url=target_url, headers=headers)
    if resp.status_code != 200:
        write_log("验证码请求失败")
        exit()
    with open(file="captchaImage.jpg", mode='wb')as f:
        f.write(resp.content)
        write_log("验证码请求成功")


def login():
    input_User_profile()
    get_captchaImage()
    code = input_Verification_code()
    global username, password
    target_url = 'https://www.livedu.com.cn/ispace4.0/checkLogin'
    data = {
        "usercode": username,
        "password": password,
        "code": code,
        "qj_flag": 1
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    login_status = json.loads(resp.text)
    if login_status.get('status') == None or login_status.get('status') == 'yzmcw':
        write_log("登录失败")
        print("信息输入的有误")
        login()
        return
    else:
        write_log("登录成功")
    print("login:", login_status['status'])


def get_all_courses():
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/queryWdkc.do'
    params = {
        'kczt': 1
    }
    global headers
    resp = session.get(url=target_url, params=params, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("获取所有课程失败")
        exit()
    with open(file="captchaImage.jpg", mode='wb')as f:
        f.write(resp.content)
        write_log("获取所有课程成功")
    soup = BeautifulSoup(resp.text, 'html.parser')
    ul_tag = soup.find(class_='zxin-b-list')
    li_tags = ul_tag.find_all('li')
    for li in li_tags:
        name = li.find(class_='zxin-b-main fl').find('h4').get_text(
        ).strip().replace('\r', '').replace('\n', '').replace('\t', '')
        progress = li.find(class_='zxin-b-scrll').find('span').get_text()
        url = li.find(class_='styu-b-r').find('a').get("onclick")
        start_index = url.find("'")
        end_index = url.find("'", start_index + 1)
        if start_index != -1 and end_index != -1:
            param = url[start_index + 1:end_index]
        else:
            write_log("课程连接解析失败")
        start_time = li.find_all('p')[0].get_text()
        end_time = li.find_all('p')[1].get_text()
        course = Course(name, progress, param, start_time, end_time)
        global Course_list
        Course_list.append(course)
        count = 0
    for course in Course_list:
        count += 1
        print(count, end='.')
        course.display_info()


def input_select():
    info = int(input("请选择你要刷课程前的序号："))
    global Course_list
    global cur_course
    cur_course = Course_list[info - 1]


def get_cur_course_info():
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/queryAllZjByKcdm.do'
    data = {
        "kcdm": cur_course.param,
        "szbj": "",
        "styflag": 1
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("获取当前课程失败")
        exit()
    else:
        resp.encoding = resp.apparent_encoding
        write_log("获取当前课程成功")
        global html
        html = resp.text


def parse():
    global html
    match = re.search(r'var zjlist = (\[.*?\]);', html, re.DOTALL)
    if match:
        zjlist_str = match.group(1)
        global Chapter_list
        Chapter_list = json.loads(zjlist_str)
        write_log("章节信息解析成功")
    else:
        write_log("章节信息解析失败")
        exit()


def get_chapter_info(chapter: dict):
    if chapter['bjdm'] == "":
        return
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/queryAllZjByKcdmIfram.do'
    params = {
        'kcdm': chapter['kcdm'],
        'bjdm': chapter['bjdm'],
        'zjdm': chapter['zjdm']
    }
    global headers
    resp = session.get(url=target_url, params=params, headers=headers)
    resp.close()
    title = chapter['zjmc']
    if resp.status_code != 200:
        write_log("获取章节信息失败" + title)
        print("获取章节信息失败")
        return
    else:
        write_log("获取章节信息成功" + title)
        print("获取章节信息成功", title)
        resp.encoding = resp.apparent_encoding
        global html
        html = resp.text


def get_duration_from_moviepy(url):
    clip = VideoFileClip(url)
    return clip.duration


def chapter_html_parse(video_demo: Video, video_ll: list):
    global html
    soup = BeautifulSoup(html, 'html.parser')
    main_content = soup.find(class_='xx-main-box')
    title = main_content.find('h4').get_text().replace(
        '\r', '').replace('\n', '').replace('\t', '')
    video_tags = main_content.find_all('video')
    if len(video_tags) != 0:
        isComplete = main_content.find(id='sp_index_1').get_text()
        video_demo.isComplete = isComplete
    video_demo.zjmc = title
    for video_tag in video_tags:
        video = video_demo
        # 获取spdm和src属性的值
        src_value = video_tag.find('source').get('src').split('#')[0]
        spdm_value = video_tag.get('spdm')
        video.spdm = spdm_value
        video.url = src_value
        video.spzsc = get_duration_from_moviepy(video.url)
        video_ll.append(video)


def get_video_params(chapter: dict):
    if chapter['bjdm'] == '':
        return
    # 创建一个样例video class，防止章节内多个视频
    video_demo = Video(bjdm=chapter['bjdm'],
                       kcdm=chapter['kcdm'], zjdm=chapter['zjdm'])
    get_chapter_info(chapter)
    video_ll = []
    chapter_html_parse(video_demo, video_ll)
    global Video_list
    Video_list.append(video_ll)


def initKcspSq(video: Video):
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/initKcspSq'
    data = {
        "kcdm": video.kcdm,
        "zjdm": video.zjdm,
        "bjdm": video.bjdm,
        "spdm": video.spdm,
        "spzsc": video.spzsc
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("初始化视频失败"+video.zjmc)
        return
    else:
        resp.encoding = resp.apparent_encoding
        write_log("初始化视频成功"+video.zjmc)
        info = json.loads(resp.text)
        print('初始化', info['msg'], video.zjmc, video.spzsc, 's')


def studentsWatchVideoRecordings(video: Video):
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/studentsWatchVideoRecordings'
    data = {
        "kcdm": video.kcdm,
        "bjdm": video.bjdm,
        "zjdm": video.zjdm,
        "zjmc": video.zjmc,
        "spdm": video.spdm
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("学习记录失败"+video.zjmc)
        return
    else:
        resp.encoding = resp.apparent_encoding
        info = json.loads(resp.text)
        write_log('学习记录', info['msg'], video.zjmc)
        if info['msg'] != '操作成功':
            print("warning:学习记录上报异常", info['msg'])


def add_and_randomize(number):
    integer_part = int(number)
    new_integer_part = integer_part + 15
    current_time_fractional = time.time() % 1
    new_decimal_part = round(current_time_fractional, 6)
    result = new_integer_part + new_decimal_part
    return result


def recordViewingTime(video: Video, flag=False):
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/studentsWatchVideoRecordings'
    if flag:
        video.spbfsc = video.spzsc
    data = {
        "kcdm": video.kcdm,
        "zjdm": video.zjdm,
        "bjdm": video.bjdm,
        "spdm": video.spdm,
        "yhdm": video.yhdm,
        "spbfsc": video.spbfsc,
        "spzsc": int(video.spzsc)
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("视频观看时间失败"+video.zjmc)
        return
    else:
        resp.encoding = resp.apparent_encoding
        write_log("视频观看时间成功"+video.zjmc)
        info = json.loads(resp.text)
        if not flag:
            print('\r视频观看时间', int(video.spbfsc), '/', int(video.spzsc),
                  info['msg'], video.zjmc, end='        ', flush=True)
        video.spbfsc = add_and_randomize(video.spbfsc)


def checkStudentSubmitVideoIsLegal(video: Video):
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/checkStudentSubmitVideoIsLegal'
    data = {
        "kcdm": video.kcdm,
        "bjdm": video.bjdm,
        "zjdm": video.zjdm,
        "zjmc": video.zjmc,
        "spdm": video.spdm,
        "gksc": int(video.spzsc)+30,
        "spzsc": int(video.spzsc)
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("checkStudentSubmitVideoIsLegal failure "+video.zjmc)
        return
    else:
        resp.encoding = resp.apparent_encoding
        write_log("checkStudentSubmitVideoIsLegal success "+video.zjmc)
        info = json.loads(resp.text)
        print('视频观看', info['msg'], video.zjmc)


def updKcspSqzt(video: Video):
    target_url = 'https://www.livedu.com.cn/ispace4.0/moocxsxx/updKcspSqzt'
    data = {
        "kcdm": video.kcdm,
        "zjdm": video.zjdm,
        "streamName": video.url.split("/")[-1]
    }
    global headers
    resp = session.post(url=target_url, data=data, headers=headers)
    resp.close()
    if resp.status_code != 200:
        write_log("updKcspSqzt failure "+video.zjmc)
        return
    else:
        resp.encoding = resp.apparent_encoding
        write_log("updKcspSqzt success "+video.zjmc)
        info = json.loads(resp.text)
        print('updKcspSqzt', info['msg'], video.zjmc)


def increaseVideoDuration():
    for chapter in Chapter_list:
        time.sleep(random.randint(0, 5))
        get_video_params(chapter)
        if chapter['bjdm'] == '':
            continue
        for video in Video_list[-1]:
            if video.isComplete == "已完成":
                continue
            initKcspSq(video)
            while video.spbfsc < video.spzsc:
                recordViewingTime(video)
                time.sleep(15)
                if random.randint(1, 100) % 30 == 0:
                    studentsWatchVideoRecordings(video)
            checkStudentSubmitVideoIsLegal(video)
            updKcspSqzt(video)
            recordViewingTime(video, True)


notice()                # 说明
login()                 # 登录获取身份
get_all_courses()       # 获取所有学习中的课程
input_select()          # 用户输入
get_cur_course_info()   # 获取选择的课程信息
parse()                 # 解析课程的章节参数
increaseVideoDuration()  # 刷视频时长
