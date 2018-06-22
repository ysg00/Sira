import requests
import json
from utils import mylog
from query import read_cookie
from query import send_request
from query import method
from utils import glob_dic
from utils import prepare
from login import login
from login import getSprint
issue_list = []
'''
send_request(url, method, headers, params, data);
'''



def addfield(dic, lst):
    reporter = {"name":lst[0]}
    priority = {"name":lst[1]}
    labels = [lst[2]]
    description = lst[3]
    assignee = {"name":lst[4]}
    fields = [reporter, priority,labels,description,assignee]
    extend = ['reporter', 'priority', 'labels', 'description', 'assignee']
    for i in range(0, len(lst)):
        if lst[i] is not '':
            dic[extend[i]] = fields[i]
    return dic
'''
lst = [project, issuetype, summary, reporter, 
    priority, lable, description, assignee, sprint]
'''
def issue_create(lst):
    url, headers = prepare('issue')
    project = {"key":lst[0]}
    issuetype = {"name":lst[1]}
    summary = lst[2]
    field = {"project":project, "summary":summary,"issuetype":issuetype}
    data = json.dumps({"fields":addfield(field,lst[3:8])})
    f, r = send_request(url, method.Post, headers, None, data)
    if not f:
        return r
    new_issue = r['key']
    if lst[8] is not '':
        pass
    getSprint()
    headers = prepare('issue')[1]
    url = '{}{}/rest/agile/1.0/sprint/{}/issue'.format(glob_dic.get_value('protocol'),glob_dic.get_value('domain'),glob_dic.get_value('sid').get(lst[8]))
    data={}
    data['issues'] = [new_issue]
    data = json.dumps(data)
    f, r = send_request(url, method.Post, headers, None, data)
    if not f:
        mylog.error(r)
        return r
    msg = 'Issue {} successfully created!'.format(new_issue)
    mylog.info(msg)
    return msg

def issue_delete(lst):
    msg = ''
    for issue in lst:
        msg += '{}\r\n'.format(issue_delete_helper(issue))
    msg += 'Done!'
    return msg

def issue_delete_helper(issue):
    url, headers = prepare('issue','/{}'.format(issue))
    f, r = send_request(url, method.Delete, headers, None, None)
    if not f:
        return 'DOING {}\r\n{}'.format(issue, r)
    msg = '{} successfully deleted!'.format(issue)
    mylog.info(msg)
    return msg


# def finduser(user):
#     url,headers = prepare('search')
#     params={'username':user}
#     f,r = send_request(url, method.Get, headers, params, None)
#     if not f:
#         return r
#     return r.get('key')

def issue_assign(lst):
    issue = lst[0]
    assignee = lst[1]
    url, headers = prepare('issue','/{}/assignee'.format(issue))
    # user_key = finduser(assignee)
    # if not user_key:
    #     return 'User not found!'
    data = '{"name":"' + assignee + '"}'

    f, r = send_request(url, method.Put, headers, None, data)
    if not f:
        return r
    msg = '{} successfully assigned to {}'.format(issue, assignee)
    mylog.info(msg)
    return msg


def issue_getComment(lst):
    issue = lst[0]
    url, headers = prepare('issue', '/{}{}'.format(issue, '/comment'))

    f, r = send_request(url, method.Get, headers, None, None)
    if not f:
        return r

    comments = r.json().get('comments',[])
    if len(comments) > 0:
        string = 'Here are the comments for ' + issue + ':\r\n'
        for com in comments:
            string += '"' + com['body'] + '"\r\n\twrote by ' + com['updateAuthor']['key'] + '\r\n\t' + com['created'] + '\r\n\t' + '(cid: ' + com['id'] + ')\r\n'
        mylog.info(string)
        return string
    else:
        mylog.info('get empty msg')
        return "There is no comment yet!"


def issue_addComment(lst):
    issue = lst[0]
    url, headers = prepare('issue','/{}/{}'.format(issue, 'comment'))
    data = ''
    with open("res/comments.json", "r") as f:
        data = json.load(f)
        data = json.dumps(data)
    f, r = send_request(url, method.Post, headers, None, data)
    if not f:
        return r
    mylog.info(r.text)
    return 'Comment(ID: ' + r.json()['id'] + ')added'


def issue_delComment(lst):
    issue = lst[0]
    cid = lst[1]
    url, headers = prepare('issue', '/{}{}{}'.format(issue, '/comment/', cid))
    f, r = send_request(url, method.Delete, headers, None, None)
    if not f:
        return r
    mylog.info('Comment {} deleted'.format(cid))
    return 'Comment deleted'


# login(['admin','admin'])
issue_create(['TEST', 'Story','This is summaryyyyyyy', '', 'Medium', '', 'This is Decriptionnnnnnn', 'ysg','TEST Sprint 1'])
# issue_assign(['TEST-38','hang'])
# issue_assign(['TEST-29','hang'])
# finduser('xp zheng')
# finduser('yuhang4')
# issue_delComment(['Test-01','10103'])
# issue_getComment(['Test-01'])
# issue_assign(['Test-01','testuser1'])
