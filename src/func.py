import json
from enum import Enum
from os import F_OK, access, mkdir
from threading import Thread

import requests

from utils import Super401, glob_dic, mylog, prepare, func_log

''' ************ login logout ************* '''

def login(lst):
    un = lst[0]
    pw = lst[1]
    url = prepare('login')[0]
    headers = {'Content-Type': 'application/json'}
    data = json.dumps({"username": un, "password": pw})
    try:
        r = requests.post(
            url,
            headers=headers,
            data=data,
            timeout=glob_dic.get_value('timeout'),
            verify=False)
        mylog.error(r.text)
        if r.status_code == 401:
            mylog.error("401 Unauthorized")
            return False, [
                '401 Unauthorized!',
                'Please make sure the username and password are correct'
            ]
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
            return (False, [
                'Login failed! Please make sure that your username and password are correct!'
            ])
        j = r.json()
        try:
            glob_dic.set_value(
                'cookie', j['session']['name'] + '=' + j['session']['value'])
        except KeyError:
            mylog.error('No session information from HTTP response\r\n' +
                        r.text)
            return (False, ['session info not found!'])
        f = open(glob_dic.get_value('cookie_path') + "cookie.txt", "w")
        f.write(glob_dic.get_value('cookie'))
        f.close()
        mylog.info("Successfully logged in as " + un)
        return (True, ["Success"])
    except requests.exceptions.RequestException as err:
        return (False, ['Login failed due to an internet error!'])


def logout():
    url, headers = prepare('logout')
    try:
        r = requests.delete(url, headers=headers, timeout=5)
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError:
            pass
    except requests.exceptions.RequestException:
        pass
    f = open(glob_dic.get_value('cookie_path') + "cookie.txt", "w")
    f.write('')
    f.close
    glob_dic.set_value('cookie', '')
    mylog.info('Successfully logged out')
    return (True, ['Successfully logged out'])


''' ************** All requests are sent through this function except login logout ************** '''

def send_request(url, method, headers, params, data):
    r = requests.Response()
    try:
        if method is method.Get:
            r = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=glob_dic.get_value('timeout'),
                verify=False)
        elif method is method.Put:
            r = requests.put(
                url,
                headers=headers,
                data=data,
                timeout=glob_dic.get_value('timeout'),
                verify=False)
        elif method is method.Delete:
            r = requests.delete(
                url,
                headers=headers,
                data=data,
                timeout=glob_dic.get_value('timeout'),
                verify=False)
        elif method is method.Post:
            r = requests.post(
                url,
                headers=headers,
                data=data,
                timeout=glob_dic.get_value('timeout'),
                verify=False)
        else:
            mylog.error('Wrong method that not suppord:' + str(method))
            return (False, ['Unknown internal error occured'])
        if r.status_code == 401:
            mylog.error("401 Unauthorized")
            raise Super401()
        try:
            r.raise_for_status()
        except requests.exceptions.HTTPError as err:
            mylog.error(r.text)
            sLst = [
                'Request denied!', 'error code: {} {}'.format(
                    str(r.status_code), str(requests.status_codes._codes[r.status_code][0]))
            ]
            try:
                lst = r.json().get('errorMessages', [])
                for errors in lst:
                    sLst.append(errors)
                dic = r.json().get('errors', {})
                for key in dic:
                    sLst.append('{} '.format(dic[key]))
            except json.JSONDecodeError:
                pass
            sLst.append('Please try again')
            return (False, sLst)
        mylog.info(r)
        try:
            try:
                s = ''
                lst = r.json()['warningMessages']
                for errors in lst:
                    s += errors + '\r\n'
                mylog.error(s)
                return (False, [s])
            except KeyError:
                return (True, r.json())
            except TypeError:
                return (True, r.json())
        except json.JSONDecodeError:
            return (True, r)
    except requests.exceptions.RequestException as err:
        mylog.error(err)
        return (False, [
            'Internet error', 'Try:',
            '\tChecking the network cables, modem, and route',
            '\tReconnecting to Wi-Fi', '\tRunning Network Diagnostics'
        ])


''' ************** Queries ************** '''
class method(Enum):
    Get = 0
    Post = 1
    Put = 2
    Delete = 3


def getTarget(fields, field):
    '''
    This function only works for identifier "name" or "key"
    fields: dict()
    field: str() (identifiers)
    '''
    ret = ''
    try:
        ret = fields.get(field)['name']
    except KeyError:
        try:
            ret = fields.get(field)['key']
        except KeyError:
            ret = fields.get(field)
    except TypeError:
        try:
            ret = str(fields.get(field)[0].get('name'))
        except IndexError:
            ret = str(fields.get(field))
        except TypeError:
            pass
        except AttributeError:
            ret = fields.get(field)
    if ret != '':
        return ret
    else:
        return 'Not available'


def getResponse(lst):
    '''
    This function used to get target field information from a list of issues
    Only information of the fields in defaultList will be returned
    '''

    defaultList = [
        'assignee', 'reporter', 'priority', 'status', 'labels', 'fixVersions','summary'
    ]
    if not lst:
        return 'Issue Not Found'
    s = ''
    for i, issue in enumerate(lst):
        s += str(issue.get('key')) + ' '
        fields = issue.get('fields')
        for j, field in enumerate(defaultList):
            s += str(getTarget(fields, field)) + ' '
            if (i != len(lst) - 1) and (j == len(defaultList) - 1):
                s += '\r\n'
    return s


@func_log
def query_issue(constraint, limit=0, order=None, **kwargs):
    url, headers = prepare('query')
    data = {}
    if order:
        order = order.lower()
        if order == 'asc':
            constraint += ' order by key ASC'
        elif order == 'desc':
            constraint += ' order by key DESC'
    else:
        constraint += ' order by updated DESC'
    
    data["jql"] = constraint
    data["startAt"] = 0
    
    if limit:
        data["maxResults"] = limit
    f, r = send_request(url, method.Post, headers, None, json.dumps(data))
    if not f:
        return r
    return getResponse(r.get('issues'))



def getInfo(r, order):
    '''
    This function used to get target field information from a list of projects
    Only information of the fields in defaultList will be returned
    '''
    lst = []
    defaultList = ['name', 'key', 'lead']
    for i, pro in enumerate(r):
        s = ''
        key = pro.get('key')
        for j, f in enumerate(defaultList):
            s += getTarget(pro, f)
            if j != len(defaultList)-1:
                s += ' ' 
        if i != len(r)-1:
            s += '\r\n'
        lst.append((key,s))
    if order and order.lower() == 'asc':
        lst.sort()
    elif order and order.lower == 'desc':
        lst.sort(reverse=True)
    s = ''
    for tup in lst:
        s += tup[1]
    return s

@func_log
def query_project(limit=0, order=None, **kwargs):
    if order:
        order = order.lower()
    param = {}
    if order == 'recent':
        if limit:
            param["recent"] = limit
        else:
            param["recent"] = 20
    param["expand"]="lead"

    url, headers = prepare('getProject')
    f,r = send_request(url, method.Get, headers, param, None)
    if not f:
        return r
    
    return getInfo(r, order)


@func_log
def query_board(key=None, limit=None, order=None, **kwargs):
    '''
    This function return all boards and order the return value.
    The return value is a string of board id adn board name
    If key is specified and valid, only one line will be returned
    '''
    url, headers = prepare('getBoard')
    f, r = send_request(url, method.Get, headers, None, None)
    lst = []
    defaultList = ['id','name']
    for info in r.get('values'):
        bid = info.get('id')
        innerlst=[]
        for f in defaultList:
            innerlst.append(info.get(f))
        lst.append(tuple(innerlst))
        if key and (bid == key):
            tup = lst.pop()
            return '{} "{}"'.format(tup[0],tup[1])
    if key:
        return 'Not found or you don\'t have permission to view this board.'
    if order and order.lower() == 'asc':
        lst.sort()
    elif order and order.lower() == 'desc':
        lst.sort(reverse=True)
    s = ''
    for i, tup in enumerate(lst):
        s += '{} "{}"'.format(tup[0],tup[1])
        if i != len(lst)-1:
            s += '\r\n'
    return s




''' ***************** Update ******************* '''
_updateBook={
    "assignee":"",
    "status":"",
    "fixVersions":"",
    "labels":"",
    "Story Points":""
}

def update_assignee(issue, info):
    url, headers = prepare('issue','/{}'.format(issue))
    data = {"fields":{"assignee":{"name":info}}}
    f, r = send_request(url, method.Put, headers, None, json.dumps(data))
    if not f:
        return r
    return 'success'


def issue_get_tansition(issue, dic):
    url, headers = prepare('issue', '/{}/transitions'.format(issue))
    f, r = send_request(url, method.Get, headers, None, None)
    if not f:
        return None
    for msg in r.get('transitions'):
        dic[msg.get('name')] = msg.get('id')
    return dic


def update_status(issue, info):
    status = info.title()
    url, headers = prepare(
        'issue', '/{}/transitions?expand=transitions.fields'.format(issue))
    data = {}
    dic = {}
    if not issue_get_tansition(issue, dic):
        return 'no transit is avaiable'
    transition = {"id": dic.get(status)}
    data = json.dumps({"transition": transition})
    f, r = send_request(url, method.Post, headers, None, data)
    if not f:
        return r
    return 'success'







if __name__ == '__main__':
    # print(query_issue(''))
    # print(query_project())
    # print(query_board())
    # print(query_board(key=4))
    print(update_status('test-88','to do'))
    pass
