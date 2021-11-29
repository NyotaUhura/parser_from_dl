import configparser
import re
import time
from requests import Session
from bs4 import BeautifulSoup
from multiprocessing import Pool


url = 'https://dl.nure.ua/my/'
config = configparser.ConfigParser()
config.read('config.conf')
login_name = config['user_info']['login']
password = config['user_info']['password']


def login():
    session = Session()
    login_url = 'https://dl.nure.ua/login/index.php'
    r_1 = session.get(url=login_url)
    pattern_auth = '<input type="hidden" name="logintoken" value="\w{32}">'
    token = re.findall(pattern_auth, r_1.text)
    token = re.findall("\w{32}", token[0])[0]
    payload = {'anchor': '',
               'logintoken': token,
               'username': login_name,
               'password': password,
               'rememberusername': 1}
    session.post(url=login_url, data=payload)
    return session


def get_courses(session):
    page = session.get(url)
    assert page.status_code == 200, 'Page status != 200'
    soup = BeautifulSoup(page.text, "html.parser")
    all_courses = soup.findAll('a', class_='dropdown-item', role='menuitem')
    res = {}
    for data in all_courses:
        if 'course' in data['href']:
            res[data.text] = data['href']
    return res


def get_course_teachers(course_url):
    page = login().get(course_url)
    soup = BeautifulSoup(page.text, "html.parser")
    all_teachers = soup.findAll('div', class_='staffinfo')
    res = []
    for data in all_teachers:
        res.append(data.findChild('h4', recursive=False).text.strip())
    return res


if __name__ == '__main__':
    logged_in_session = login()
    courses_list = get_courses(logged_in_session)
    processes = []

    start_time = time.time()

    with Pool(10) as p:
        res = p.map(get_course_teachers, list(courses_list.values()))

    print("--- %s seconds ---" % (time.time() - start_time))
    print(dict(zip(courses_list.keys(), res)))
