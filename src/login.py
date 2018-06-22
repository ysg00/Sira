import json
from threading import Thread

import requests

from query import method, send_request
from utils import (Super401, glob_dic, mylog,
                   prepare)

''' lst = ['username','password'] '''
def login(lst):
    un = lst[0]
    pw = lst[1]
    url = prepare('logout')[0]
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"username":un, "password":pw})
    try:
        r = requests.post(url, headers=headers, data=data, timeout=glob_dic.get_value('timeout'),verify=False)
        mylog.error(r.text)
        if r.status_code == 401:
            mylog.error("401 Unauthorized")
            raise Super401
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            mylog.error(err)
            try:
                errmsg = r.json()['errorMessages'][0]
                mylog.error(errmsg)
            except KeyError:
                pass
            except json.decoder.JSONDecodeError:
                pass
            return (
                False,
                'Login failed! Please make sure that your username and password are correct!'
            )
        j = r.json()
        try:
            glob_dic.set_value('cookie', j['session']['name'] + '=' + j['session']['value'])
        except KeyError:
            mylog.error('No session information from HTTP response\r\n' +
                          r.text)
            return (False, 'session info not found!')
        f = open(glob_dic.get_value('cookie_path') + "cookie.txt", "w")
        f.write(glob_dic.get_value('cookie'))
        f.close
        mylog.info("Successfully logged in as "+un)
        thr = Thread(target=download,args=())
        thr.start()
        return (True, "Success")
    except requests.exceptions.RequestException as err:
        mylog.error(err)
        return (False, 'Login failed due to an internet error!')


def logout():
    url, headers = prepare('logout')
    r = requests.delete(url,headers=headers)
    try:
        r.raise_for_status()
    except requests.exceptions.HTTPError:
        return (True, 'No account logged in yet')
    f = open(glob_dic.get_value('cookie_path') + "cookie.txt", "w")
    f.write('')
    f.close
    glob_dic.set_value('cookie','')
    mylog.info('Successfully logged out')
    return (True, 'Successfully logged out')

def goInto(lst, key, field):
    target = []
    for element in lst:
        tmp = element.get(field,'')
        if (tmp is not '') and (tmp not in target):
            target.append(tmp)
    if target:
        glob_dic.tips.set_value(key,target)
        return True
    return False

def getProject():
    url,headers = prepare('getProject')
    f, r = send_request(url, method.Get, headers, None, None)
    if f:
        return goInto(r, 'project', 'key')

def getBoard():
    url,headers = prepare('getBoard')
    f, r = send_request(url, method.Get, headers, None, None)
    if f:
        return goInto(r.get('values'), 'board', 'id')


def getSprint():
    headers = prepare('getSprint')[1]
    lst = []

    if not getBoard():
        return False
    for boardid in glob_dic.tips.get_value('board'):
        url = 'http://' + glob_dic.get_value('domain') + '/rest/agile/1.0/board/'+str(boardid)+'/sprint'
        f, r = send_request(url, method.Get, headers, None, None)
        if not f:
            return False
        lst += r.get("values")
    if not goInto(lst, 'sprint', 'name'):
        return False
    # print(lst)
    glob_dic.set_value('sid',{})
    for msg in lst:
        glob_dic.get_value('sid')[msg['name']] = msg['id']
    return True


def getStatus():
    url,headers = prepare('getStatus')
    f, r = send_request(url, method.Get, headers, None, None)
    if f:
        return goInto(r, 'status', 'name')

def getType():
    url,headers = prepare('getType')
    f, r = send_request(url, method.Get, headers, None, None)
    if f:
        return goInto(r, 'type', 'key')


def getIssuetype():
    url,headers = prepare('getIssuetype')
    f, r = send_request(url, method.Get, headers, None, None)
    if f:
        return goInto(r, 'issuetype', 'name')

def getAssignee():
    url,headers = prepare('getAssignee')
    f, r = send_request(url, method.Get, headers, None, None)
    if f:
        return goInto(r, 'assignee', 'key')

def getPriority():
    url, headers = prepare('getPriority')
    f, r = send_request(url, method.Get, headers, None, None)
    print(r)
    if f:
        return goInto(r, 'priority', 'name')

def getVersion():
    getProject()
    lst = []
    for p in glob_dic.tips.get_value('project'):
        url,headers = prepare('getVersion')
        url += '/{}/versions'.format(p)
        f, r = send_request(url, method.Get, headers, None, None)
        if not f:
            return False
        lst += r
    return goInto(lst, 'versions', 'name')


def download():
    getProject()
    getSprint()
    getType()
    getIssuetype()
    getStatus()
    getAssignee()
    getPriority()
    f = open('tables.json','w+')
    f.write(json.dumps(glob_dic.tips.dic))
    f.close()
    # pass

def tryload():
    f = open('tables.json', 'r')
    data = json.loads(f.read())
    f.close()
    glob_dic.tips.set_value('project',data.get('project'))
    glob_dic.tips.set_value('type',data.get('type'))
    glob_dic.tips.set_value('issuetype',data.get('issuetype'))
    glob_dic.tips.set_value('sprint',data.get('sprint'))
    glob_dic.tips.set_value('status',data.get('status'))

try:
    tryload()
except FileNotFoundError as fe:
    mylog.error(fe)
    download()
