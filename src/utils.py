"""
usage:
from myLog import mylog

...
mylog.info('msg')
mylog.debug('msg')
mylog.error('msg')
...

"""
import json
import logging
from os import F_OK, access, listdir, mkdir, remove
from time import localtime, strftime, strptime


log_directory = "log/"
if not access(log_directory, F_OK):
    mkdir(log_directory)
time_format = '%d(%b)%Y %H-%M-%S'
logformat = '%(asctime)s.%(msecs)d %(levelname)-8s [%(filename)s:%(lineno)d]\r\t%(message)s\r\n'
min_time = localtime()
logging.basicConfig(
    filename='{}{}.log'.format(log_directory,
                               strftime(time_format, min_time)),
    format=logformat,
    datefmt=time_format
)
log_list = listdir(log_directory)
if len(log_list) > 10:
    for s in listdir(log_directory):
        try:
            log_time = strptime(s, time_format + ".log")
            if log_time < min_time:
                min_time = log_time
        except ValueError as ve:
            remove(log_directory + s)
    remove('{}{}.log'.format(log_directory,
                                strftime(time_format, min_time)))
mylog = logging.getLogger(__name__)
mylog.setLevel(logging.DEBUG)

func_enter_log_format = \
"""Entered method {}.{} with the following positional arguments:
\t\t{},
\tand the following keyword arguments:
\t\t{}"""

func_return_log_format = \
"""Exited method {}.{} with the following return value(s):
\t\t{}"""

def func_log(method):
    def log(*args, **kwargs):
        info = func_enter_log_format.format(method.__module__,
                                            method.__name__,
                                            args,
                                            kwargs)
        mylog.info(info)
        result = method(*args, **kwargs)
        info = func_return_log_format.format(method.__module__,
                                            method.__name__,
                                            result)
        mylog.info(info)
        return result
    return log

def overrides(interface_class):
    def overrider(method):
        assert (method.__name__ in dir(interface_class))
        return method
    return overrider


def asserts(expression, msg):
    try:
        assert expression, msg
    except AssertionError as err:
        mylog.error(err)
        return False
    return True

def write_memo_log(*args):
    info = "Program exited with the following attributes:\n"
    info_line = "\t{}:\n\t\t{}\n"
    for cls in args:
        for attr in dir(cls):
            value = getattr(cls, attr)
            if not callable(value) and not attr.startswith("__"):
                info += info_line.format("{}.{}".format(type(cls), attr),
                                         value)
    mylog.info(info)



class Super401(Exception):
    def __init__(self):
        self.err = 'Error Unauthorized. please login in again'
        Exception.__init__(self, self.err)


class glob():
    def __init__(self, dic):
        self.dic = dic
        self.set_value('jira', 'lnvusjira.lenovonet.lenovo.local')
        self.set_value('cookie_path', '')
        self.set_value('cookie', '')


    def set_value(self, key, value):
        self.dic[key] = value

    def get_value(self, key, defValue=None):
        try:
            return self.dic[key]
        except KeyError:
            return defValue

def read_cookie():
    if glob_dic.get_value('cookie', '') == '':
        try:
            with open(glob_dic.get_value('cookie_path') + "cookie.txt",
                      "r") as f:
                glob_dic.set_value('cookie', f.read())
                f.close()
        except FileNotFoundError as err:
            mylog.error(err)
            raise Super401
    return glob_dic.get_value('cookie')

def prepare(s, extend=None):
    if s != 'login':
        headers_book.get(s)['cookie'] = read_cookie()
    if extend is not None:
        return (address_book.get(s) + extend, headers_book.get(s))
    return (address_book.get(s), headers_book.get(s))


glob_dic = glob({})

# domain ='lnvusjira.lenovonet.lenovo.local'

domain = '10.176.120.165:8080'
protocol = 'http://'
address_book = {
        'login': protocol + domain + '/rest/auth/1/session',
        'logout': protocol + domain + '/rest/auth/1/session',
        'getProject': protocol + domain + '/rest/api/2/project',
        'getBoard': protocol + domain + '/rest/agile/1.0/board',
        'getStatus': protocol + domain + '/rest/api/2/status',
        'getType': protocol + domain + '/rest/api/2/project/type',
        'getIssuetype': protocol + domain + '/rest/api/2/issuetype',
        'getAssignee': protocol + domain + '/rest/api/2/user/search',
        'getPriority': protocol + domain + '/rest/api/2/priority',
        'query': protocol + domain + '/rest/api/2/search',
        'query_number': protocol + domain + '/rest/agile/1.0/issue',
        'issue': protocol + domain + '/rest/api/2/issue',
        'search': protocol + domain + '/rest/api/2/user',
        'getVersion': protocol + domain + '/rest/api/2/project',
        'getSprint':protocol + domain + '/rest/agile/1.0/sprint',
        'assign_sprint': protocol + domain + '/rest/agile/1.0/sprint',
        'createmeta': protocol + domain + '/rest/api/2/issue/createmeta',
        'getField': protocol + domain + '/rest/api/2/field',
        'getEstimation': protocol + domain + '/rest/agile/1.0/issue'
    }

headers_book = {
    'getEstimation':{
        'Accept': 'application/json',
        'cookie': ''
    },
    'createmeta':{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'cookie': ''
    },
    'permission':{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'cookie': ''
    },
    'mypermission':{
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'cookie': ''
    },
    'logout': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getProject': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getBoard': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getStatus': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getSprint': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getType': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getAssignee': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getPriority': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getIssuetype': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'query': {
        'Content-Type': 'application/json',
        'cookie': ''
    },
    'query_number': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'issue': {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'cookie': ''
    },
    'search': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'getVersion': {
        'Accept': 'application/json',
        'cookie': ''
    },
    'assign_sprint': {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
        'cookie': ''
    },
    'getField':{
        'Accept': 'application/json',
        'cookie': ''
    }
}


