# import json

defaultList = [
    'issuetype', 'assignee', 'status', 'fixVersions', 'summary'
]
defaultHeader = [
    'IssueID', 'Type', 'Assignee', 'Status', 'FixVer.', 'Summary'
]


# def getIssue(s, key):
#     j = json.loads(s)
#     issue = []
#     try:
#         issue = j['issues']
#     except KeyError:
#         pass
#     if key is None:
#         return issue
#     else:
#         for i in range(0, len(issue)):
#             if issue[i]['key'] == key:

#                 return [issue[i]]
#         return None


'''
type | number | title | assignee | sprint | status | fixed version | project
'''


def getField(issue, field):
    if field is None:
        return defaultField(issue)
    if isinstance(issue['fields'][field], dict):
        return {field: issue['fields'][field]['name']}
    return {field: issue['fields'][field]}


def defaultField(issue):
    global defaultList
    dic = {}
    for i in defaultList:
        dic.update(getField(issue, i))
    return dic


def dtos(dic, issue):
    string = ('{}'.format(issue)).ljust(12, ' ') + '|  '
    for i in dic:
        # string += format(' {} '.format(dic[i]),' >20')
        if i is not 'summary':
            string += ('{}'.format(dic[i])).ljust(12, ' ') + '|  '
        else:
            string += ('{}'.format(dic[i]))
    return string


def getString(j):
    global defaultList
    string = ''
    issue_lst = []
    try:
        issue_lst = j['issues']
        return j['warningMessages']
    except KeyError:
        pass
    if len(issue_lst) > 0:
        for i in defaultHeader:
            string += '{}'.format(i).ljust(15, ' ')
        string += '\r\n'
        for i in range(0, len(issue_lst)):
            try:
                if i == len(issue_lst) - 1:
                    string += dtos(
                        getField(issue_lst[i], None), issue_lst[i]['key'])
                else:
                    string += dtos(
                        getField(issue_lst[i], None),
                        issue_lst[i]['key']) + '\r\n'
            except KeyError as err:
                return_val = 'given field "{}" not found'.format(err)
                return return_val
        return string
    else:
        return 'Issue not Found'

