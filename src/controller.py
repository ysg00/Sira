import re
import threading
import xml.etree.ElementTree as ET
import login
import query
import issueOps
from prompter import Prompter
from utils import Super401, mylog


class SiraController():

    """The controller class which can handle input command and pass the corresponding function result

    public methods:
        processInput(self, instance, string) -> None
        closeinteractive -> None

    *view* is the UI object.
    *separater* is a regular expression to split command.
    *tree* holds the xml DOM struture.
    *position* holds the current node of xml
    *args* holds parsed parameters
    *no_need_login" contains the commands that user can call without login

    """
    normal_cursor = ">"
    no_need_login = ["sira", "login", "exit", "clear"]

    def __init__(self, view, model):
        self.view = view
        self.model = model
        self.separater = re.compile("\\s+")    # command separater
        self.args = []         # hold the args of command
        self.interactive = False
        self.tree = ET.parse("res/glossary.xml").getroot()
        self.position = self.tree   # the current position of tree
        self.prompter = Prompter()

    def processInput(self, string):
        """According to the xml DOM structure, parser the input from UI, exec function and display the result

        *string* is the command from UI

        """
        self._cal(string)
        # try:
        #     self._cal(string)
        # except Exception as err:
        #     mylog.error(err)
        #     self._sendinfo("error while processing")

    def closeinteractive(self):
        """Close the interactive mode by clear cache and display "interactive mode closed"

        This function only work in interactive mode.

        """
        if(self.position is None or self.position == self.tree):
            pass
        self._clearcache()
        self.view.set_command_mode(True)
        self.view.commandText.readonly = False
        self.view.info = ["interactive mode closed"]
        self.view.print_header()
    
    def _cal(self, command): 
        # pass when command is empty in non-interactive mode
        if len(command) <= 0:
            if self.position == self.tree:
                self.view.print_header()
                return

        tokens = self.separater.split(command.strip())
        for i, token in enumerate(tokens):
            pre_position = self.position
            for child in self.position.getchildren():
                if child.tag == "keyword" and child.attrib['name'] == token:
                    # exclude keywords need to login
                    if (not self.view.username) and (token not in self.no_need_login):
                        self._sendinfo("Please login first")
                        return
                    # exclude login keyword if have logged in
                    elif self.view.username and token == "login":
                        self._sendinfo("already logged in as " + self.view.username)
                        return
                    else:
                        self.position = child
                        break
                elif child.tag == "optional" or child.tag == "required":
                    # required field can't be empty
                    if child.tag == "required" and not token:
                        return
                    if pre_position.tag != "keyword" and self.interactive and i != 0:
                        break
                    else:
                        self.position = child
                        self.args.append(token)
                    break
            # do not extend deep
            if pre_position == self.position:
                if pre_position.tag != "keyword" and self.args:
                    self._increpara(token)
                else:
                    self._sendinfo("error command")
                    return
        # pass if has sub-node ,exec function if has't
        if self.position.find("./required") or self.position.find("./optional"):
            # call function first if exist
            func = self.position.find("./function")
            if func is not None:
                if func.attrib['object']:
                    getattr(eval(func.attrib['object']),func.attrib['name'])()
                else:
                    getattr(self,func.attrib['name'])()
            # display intseractive text
            interactive = self.position.find("./interactive")
            self.interactive = True
            self.view.set_command_mode(False)
            self.view.info = [interactive.text] if interactive is not None else [""]
        elif self.position.find("./keyword"):
            # display intseractive text
            interactive = self.position.find("./interactive")
            if interactive is not None:
                self.interactive = True
                self.view.set_command_mode(False)
                self.view.info = ["-"]
            else:
                self._sendinfo("error command")
        else:
            self.view.commandText.readonly = True
            functag = self.position.find("./function")
            if functag.attrib['multi-thread'] == 'True':
                threading.Thread(None,self._execfunc).start()
            else:
                if functag.attrib['name'] == "on_clear":
                    self.view.commandText.readonly = False
                    self.view.print_header()
                    self.view.on_clear()
                    self._clearcache()
                else:
                    self._execfunc()

    def _execfunc(self):
        """Call the function after parsing

        It will change the value of username which view holds if the function is login.
        Login function will pass 2 args contains status and result(str).

        """
        try:
            functag = self.position.find("./function")
            obj = functag.attrib['object']
            name = functag.attrib['name']
            if self.args:
                result = getattr(eval(obj), name)(self.args)
            else:
                result = getattr(eval(obj), name)()
            # set cursor value to username when login successd
            if name == "login" and result[0]:
                self.view.username = self.args[0]
            elif (name == "login" and not result[0]) or name == "logout":
                self.view.username = ""
            result = result[1] if name == "login" else result
            # display result
            self._sendinfo(result)
        except Super401 as autherr:
            self.view.username = ""
            login.logout()
            self._sendinfo(autherr.err)
        except Exception as err:
            mylog.error(err)

    def _sendinfo(self, msg):
        self._clearcache()
        self.view.commandText.readonly = False
        self.view.set_command_mode(True)
        if msg:
            self.view.info = [msg]
        self.view.print_header()

    def _clearcache(self):
        self.position = self.tree
        self.interactive = False
        self.args.clear()

    def _increpara(self, s):
        if self.args:
            arg = self.args.pop()
            arg = arg + " " + s
            self.args.append(arg)
        else:
            self.args.append(s)

    def auto_complete(self, command):
        self.view.option = self.prompter.auto_complete(self.position,self.interactive,command)
