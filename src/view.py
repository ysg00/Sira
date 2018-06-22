from os import F_OK, access, listdir

import kivy.properties as kp
from kivy.app import App
from kivy.config import ConfigParser
from kivy.lang import Builder
from kivy.uix.settings import Settings, SettingsWithSidebar
from kivy.uix.widget import Widget

from advancedtextinput import AdvancedTextInput
from controller import SiraController
from utils import asserts, mylog, overrides


class SiraApp(App):

    """The application class for Sira application, working as a view.

    extends:
        kivy.app.App

    Instance Variables:
        Class-scope Variables:
            completion_start -- kivy.properties.NumericProperty (default 0)
            from_space -- kivy.properties.BooleanProperty (default True)
            header -- kivy.properties.StringPorperty (default None)
            info -- kivy.properties.ListProperty (default [])
            option -- kivy.properties.ListProperty (default [])
            protected_text -- kivy.properties.StringPorperty (default None)
            start_indices -- kivy.properties.ListProperty (default [])
            tab_index -- kp.NumericProperty (default -1)
            username -- kivy.properties.StringPorperty (default None)

        Method-established Variables:
            commandText -- advancedtextinput.AdvancedTextInput (default None)
            config_func_dict -- dict((str, str) : callable)

    Public Methods:
        Overrided from kivy.app.App:
            __init__(self, **kwargs) -> None
            build(self) -> advancedtextinput.AdvancedTextInput()
            build_config(self, config.ConfigParser) -> None
            build_settings(self, kivy.uix.settings.Settings) -> None
            on_config_change(self, config.ConfigParser, str, str, str) -> None

        Original:
            on_clear(self) -> None
            print_header(self) -> None
            set_command_mode(self, bool) -> None
            set_controller(self, controller.SiraController) -> None
            set_pwd_mode(self) -> None

    Private Methods:
        _get_font_path(self, str) -> str
        _on_cmd_idf(self, str) -> None
        _on_command(self, advancedtextinput.AdvancedTextInput) -> None
        _on_font_name(self, str) -> None
        _on_font_size(self, str) -> None
        _on_reduce_option(self, advancedtextinput.AdvancedTextInput) -> bool
        _on_space(self, advancedtextinput.AdvancedTextInput) -> bool
        _on_switch_option(self,
                          advancedtextinput.AdvancedTextInput,
                          str) -> bool
        _on_tab(self, advancedtextinput.AdvancedTextInput) -> None
        _reset_header(self, str, str) -> None
        _select_next_option(self, str) -> None
        _stop_completion(self, advancedtextinput.AdvancedTextInput) -> None
        _stop_interaction(self, advancedtextinput.AdvancedTextInput) -> None
        

    Events:
        `on_info`
            Fired when info is changed. This will print everything, one element
            per line, in the {@code info} to the command window and move the
            cursor to the end of text.

        `on_option`
            Fired when option is changed. This will print everything, one
            element per line, in the {@code info} to the command window without
            moving the cursor.

        `on_username`
            Fired when username is changed. This will change and write the
            sira.ini (Section: Text, Key: username) based on its value, and call
            _reset_header to preserve [convention #1.1].

    Property Driven Methods:
        on_info(self, advancedtextinput.AdvancedTextInput, list) -> None
        on_option(self, advancedtextinput.AdvancedTextInput, list) -> None
        on_username(self, advancedtextinput.AdvancedTextInput, str) -> None

    Conventions:
        {
            TODO: self.commandText.last_row
        }
    """

    completion_start = kp.NumericProperty(0)
    """TODO: here
    """

    from_space = kp.BooleanProperty(True)
    """TODO: here
    """

    header = kp.StringProperty(None)
    """Kivy string property to store the command header.

    [convention #1]: {
        (self.header = (self.username
            + self.config.get("Text", "cmd_identifier")))           #1.1
        }
    
    [callback]: None
    """

    info = kp.ListProperty([])
    """Kivy list property to store buffered results. When info changes,
    function on_info will be dispatched, and self.commandText will print
    every element in info on seperate lines.

    [convention #2]: {
            (for line in self.info: isinstance(line, str))          #2.1
        &&  (self.info = []) after self.on_info                     #2.2
    }

    [callback]: on_info
    """

    option = kp.ListProperty([])
    """TODO
    """

    options_per_line = kp.NumericProperty(7)
    """TODO: both here and class doc
    """

    page_index = kp.NumericProperty(0)
    """TODO: both here and class doc
    """

    protected_text = kp.StringProperty(None)
    """Kivy string property to store the protected_text of the current
    command line.

    [convention #3]: {
        (self.protected_text = self.commandText._lines[instance.last_row])         #3.1
    }

    [callback]: self.commandText.protected_len (from res/sira.kv)
    """

    start_indices = kp.ListProperty([])
    """TODO: both here
    """

    tab_index = kp.NumericProperty(-1)
    """TODO: both here
    """

    username = kp.StringProperty(None)
    """Kivy string property to store username.

    [convention #4]: {
            [convention #1.1]
        &&  (self.username = "") iff [no user is logged in]         #4.1
    }

    [callback]: on_username
    """

    @overrides(App)
    def __init__(self, **kwargs) -> None:
        """Constructor of SiraApp.

        [ensures]:  isinstance(self.__events__, list),
                    isinstance(self.config_func_dict)
        [calls]:    super(SiraApp, self).__init__
        """
        super(SiraApp, self).__init__(**kwargs)
        self.__events__ = ["on_info", "on_option", "on_username"]
        # Element Constraint: {(section, key): func}
        self.config_func_dict = {
            ("Text", "cmd_identifier"): self._on_cmd_idf,
            ("Text", "font_size"): self._on_font_size,
            ("Text", "font_name"): self._on_font_name
        }

    @overrides(App)
    def build(self) -> Widget:
        """Builder of the application interface, called after build_config().

        [requires]: isinstance(self.config, kivy.config.Config)
                    [see [ensures] of build_config]
        [ensures]:  self.header = self.config.get("Text", "username")
                                  + self.config.get("Text", "cmd_identifier)
                    isinstance(self.commandText, Widget)
                    self.commandText.text = self.header
                    self.protected_text = self.header
        [calls]:    _reset_header
                    [reset self.commandText.protected_len]
        """
        if not asserts(isinstance(self.config, ConfigParser),
                       "self.config is not initialized."):
            return

        self.settings_cls = SettingsWithSidebar
        self.username = self.config.get("Text", "username")
        self._reset_header(self.username,
                           self.config.get("Text", "cmd_identifier"))
        self.protected_text = self.header
        self.commandText = Builder.load_file("res/sira.kv")
        return self.commandText

    @overrides(App)
    def build_config(self, config: ConfigParser) -> None:
        """Public function builds self.config from src/sira.ini if it exists,
        otherwise sets self.config with default values and writes in
        src/sira.ini.

        [ensures]:  self.config is not None
                    [self.config has all attributes in its source file]
                    [At least, the following attributes exist:
                        "Text", "user_name"
                        "Text", "cmd_identifier"
                        "Text", "font_size"
                    ]
        """
        Text = {
            "cmd_identifier": ">",
            "font_size": "14",
            "font_name": "Monaco",
            "username": ""
        }
        config.setdefaults("Text", Text)

    @overrides(App)
    def build_settings(self, settings: Settings) -> None:
        """Builds and adds custom setting pannels to original settings,
        called when the user open settings for the first time.

        [requires]: isinstance(self.config, kivy.config.Config)
                    [see [ensures] of build_config]
        """
        if not asserts(isinstance(self.config, ConfigParser),
                       "self.config is not initialized."):
            return
        settings.add_json_panel("Text Option", self.config,
                                filename="res/sira.json")

    @overrides(App)
    def on_config_change(self,
                         config: ConfigParser,
                         section: str,
                         key: str,
                         value: str) -> None:
        """Fires when configs change.

        [requires]: config = self.config
                    (for all config where config = self.config, ((section, key)
                        in self.config_func_dict.keys()))
        [calls]:    [corresponding functions in self.config_func_dict]
        """

        if config == self.config:
            if not asserts((section, key) in self.config_func_dict.keys(),
                           "({}, {}) is not a key pair in self.config_func_dict".format(section, key)):
                return
            self.config_func_dict[(section, key)](value)

    def on_clear(self) -> None:
        """Public function to clear the screen. This methods essentially
        scrolls all historical texts above the window.
        """
        instance = self.commandText
        instance.scroll_y = (instance.last_row) * instance.line_height

    def print_header(self) -> None:
        """Public function to print self.header in self.commandText.

        [requires]: self.header is not None
                    self.commandText is not None
        [ensures]:  [self.header displays as the last part in self.commandText]
                    self.protected_text = self.header
        [calls]:    [reset self.commandText.protected_len]
        """
        if not asserts(self.header is not None,
                       "self.header must be initialized before calling print_header."):
            return
        if not asserts(self.commandText is not None,
                       "self.commandText must be initialized before callingprint_header."):
            return

        obj = self.commandText

        obj.insert_text("\n" + self.header)
        self.protected_text = self.header
        obj.last_row = len(obj._lines) - 1
        obj.last_row_start = len(obj.text) - len(obj._lines[obj.last_row])
        obj.on_cursor(obj, obj.cursor)

    def set_command_mode(self, value: bool) -> None:
        """Public function to set self.commandText.command_mode to value.

        [ensures]:  self.commandText.command_mode = value
        """
        self.commandText.command_mode = value

    def set_controller(self, controller: SiraController) -> None:
        """Public function to set self.controller to controller.

        [ensures]:  self.controller = controller
        """
        self.controller = controller

    def set_pwd_mode(self) -> None:
        """Public function to set self.commandText.password_mode to True.

        [ensures]:  self.commandText.password_mode = True
        """
        self.commandText.password_mode = True

    def _clear_options(self, instance: AdvancedTextInput) -> None:
        """TODO: both here and class doc
        """
        instance.cancel_selection()
        start = instance.text.rindex('\n')
        end = len(instance.text)
        instance.select_text(start, end)
        instance.delete_selection()

    def _get_font_path(self, font_name) -> str:
        """Private function to search the path of font file based on font_name.

        [returns]:  "Roboto" if ["res/fonts/" directory is not readable]
                                or [not font file matches font_name]
                                or [the matched file is not readable]
                    "res/fonts/{font_name}.*" if [there is a font file matches
                                                  font_name]
        """
        directory = "res/fonts/"
        if not access(directory, F_OK):
            return "Roboto"
        file_list = listdir(directory)
        for file_name in file_list:
            if font_name.lower() in file_name.lower():
                path = directory + file_name
                break
        return path if access(path, F_OK) else "Roboto"

    def _on_cmd_idf(self, value: str) -> None:
        """Private function fired when cmd_identifier is changed through
        self.config.

        [ensures]:  reset self.header to preserve [convention #1.1]
        [calls]:    _reset_header
        """
        self._reset_header(self.username, value)

    def _on_command(self, instance: AdvancedTextInput) -> bool:
        """"Privated function fired when self.commandText.on_text_validate is
        called, in other words, when users hit the 'enter' key. This property
        is established by res/sira.kv.

        [ensures]:  instance.last_row > 0
                    instance.protected_len <= len(instance._lines[instance.last_row])
                    instance.password_mode = False
                    instance.history_stack.traversal =
                        instance.history_stack.traversal_dummy
        [calls]:    instance.history_stack.reset_traversal
                    self.controller.processInput
        """
        string = instance._lines[instance.last_row][instance.protected_len:]
        if instance.password_mode:
            string = instance.password_cache
            instance.password_mode = False
        elif instance.command_mode and string != "":
            instance.history_stack.push(string)
        instance.history_stack.reset_traversal()
        self.controller.processInput(string)
        instance.on_cursor(instance, instance.cursor)
        return True

    def _on_display_options(self,
                            instance: AdvancedTextInput,
                            behavior: str,
                            option: list) -> bool:
        """TODO: here and class doc
        """
        # display options based on behavior
        instance.do_cursor_movement("cursor_end", control=True)
        cursor = instance.cursor
        if behavior == "init":
            self.page_index = 0
        else:
            self._clear_options(instance)
            self.tab_index = -1
            next_index = self.page_index + self.options_per_line\
                         if behavior == "next"\
                         else self.page_index - self.options_per_line
            self.page_index = max(0, next_index)\
                              if next_index < len(option)\
                              else self.page_index
        end_index = self.page_index + self.options_per_line\
                    if self.page_index + self.options_per_line <= len(option)\
                    else len(option)
        instance.insert_text("\n" + " ".join(option[self.page_index:end_index]))
        instance.cursor = cursor
        # calc start indices of displayed options
        index = 0
        self.start_indices.clear()
        for s in option[self.page_index:end_index]:
            self.start_indices.append(index)
            index += len(s) + 1
        return True

    def _on_font_name(self, value: str) -> None:
        """"Privated function fired when font_name is changed through
        self.config.
        """
        self.commandText.font_name = self._get_font_path(value)

    def _on_font_size(self, value: str) -> None:
        """Privated function fired when font_size is changed through
        self.config.

        [ensures]:  self.commandText.font_size = int(value)
        """
        self.commandText.font_size = int(value)

    def _on_reduce_option(self, instance: AdvancedTextInput) -> bool:
        """TODO: both here and class doc
        """
        copy = list()
        instance.do_cursor_movement("cursor_end", control=False)
        end = instance.cursor_index(instance.cursor)
        word_truc = instance.text[self.completion_start:end]
        for s in self.option:
            if s.lower().startswith(word_truc.lower()):
                copy.append(s)
        self._stop_completion(instance)
        self.option = copy

    def _on_space(self, instance: AdvancedTextInput) -> bool:
        """TODO: both here and class doc
        """
        if instance.completion_mode:
            self._stop_completion(instance)
        c_index = instance.cursor_index(instance.cursor) - 1
        if instance.last_row_start + instance.protected_len != c_index\
                and instance.text[c_index - 1] != " ":
            string = instance._lines[instance.last_row][instance.protected_len:]
            self.from_space = True
            self.controller.auto_complete(string)
        return True

    def _on_switch_option(self,
                          instance: AdvancedTextInput,
                          direction: str) -> bool:
        """TODO: here
        """
        self._select_next_option(direction)

    def _on_tab(self, instance: AdvancedTextInput) -> bool:
        """TODO
        """
        if instance.password_mode:
            return True
        if instance.completion_mode:
            self._select_next_option("tab")
        else:
            string = instance._lines[instance.last_row][instance.protected_len:]
            self.from_space = False
            self.controller.auto_complete(string)
        return True

    def _reset_header(self, username: str, identifier: str) -> None:
        """Private funciton to reset self.header based on username and
        identifier to preserve [convention #1.1]

        [ensures]:  [convention #1.1]
        """
        self.header = username + identifier

    def _select_next_option(self, direction: str) -> None:
        """TODO
        """
        instance = self.commandText
        # update self.tab_index according to direction
        if direction == "tab":
            self.tab_index = self.tab_index + 1\
                             if self.tab_index < len(self.start_indices) - 1\
                             else 0
        elif direction == "left":
            self.tab_index = self.tab_index - 1\
                             if self.tab_index > 0\
                             else 0
        elif direction == "right":
            self.tab_index = self.tab_index + 1\
                             if self.tab_index < len(self.start_indices) - 1\
                             else len(self.start_indices) - 1
        # delete and insert next option
        instance.cancel_selection()
        start = self.completion_start
        end = instance.last_row_start + len(instance._lines[instance.last_row])
        instance.select_text(start, end)
        instance.delete_selection()
        instance.do_cursor_movement("cursor_end", control=True)
        instance.insert_text(self.option[self.page_index + self.tab_index])
        # select next option
        last_char_return = instance.text.rindex("\n")
        start = last_char_return + self.start_indices[self.tab_index] + 1
        end = start + len(self.option[self.page_index + self.tab_index])
        instance.select_text(start, end)

    def _stop_completion(self, instance: AdvancedTextInput) -> None:
        """TODO: here & class doc
        """
        self._clear_options(instance)
        instance.completion_mode = False
        self.tab_index = -1
        self.option = []
        self.start_indices = []

    def _stop_interaction(self, instance: AdvancedTextInput) -> None:
        """Private function to interrupt interactive mode. This function will
        be fired when the user hit control-C.

        [ensures]:  instance.password_mode = False
                    instance.command_mode = True
        [calls]:    self.controller.closeinteractive
        """
        if not self.commandText.command_mode:
            self.controller.closeinteractive()
            instance.password_mode = False
            instance.command_mode = True

    def on_info(self, instance: App, info: list) -> None:
        """Property driven function, fired when info is changed. This function
        automatically prints all elements in info on seperate lines in
        this.commandText.

        [requires]: [convention #2.1]
        [ensures]:  [convention #2.2]
                    (self.commandText.text = $self.commandText.text + '\n' 
                                             + \n'.join(info))
        [calls]:    on_info (recursively once)
        """
        if self.info == []:
            return
        obj = self.commandText
        for s in info:
            if not asserts(isinstance(s, str),
                           "(for line in self.info: isinstance(line, str))."):
                return
        obj.do_cursor_movement("cursor_end", control=True)
        self.protected_text = info[-1]
        for s in info:
            obj.insert_text("\n" + str(s))
        obj.last_row = len(obj._lines) - 1
        obj.last_row_start = len(obj.text) - len(obj._lines[obj.last_row])
        obj.on_cursor(obj, obj.cursor)
        self.info = []

    def on_option(self, instance: App, option: list) -> None:
        """TODO
        """
        obj = self.commandText
        if option == []:
            obj.completion_mode = False
            return
        obj.completion_mode = True
        self._on_display_options(obj, "init", option)
        # calc the start index of the completion part
        search_start = obj.last_row_start + obj.protected_len
        search_end = obj.last_row_start\
                     + len(obj._lines[obj.last_row])
        try:
            self.completion_start = obj.text.rindex(" ",
                                                    search_start,
                                                    search_end) + 1
        except ValueError:
            self.completion_start = search_start
        if not self.from_space:
            self._select_next_option("tab")

    def on_username(self, instance: App, value: str) -> None:
        """Property driven function, fired when username is changed. This
        function writes the new value in self.config and its corresponding
        config files.

        [requires]: self.config is not None
                    [convention #4.1] (unchecked)
        [ensure]:   self.config.get("Text", "username") = value
                    [convention #1.1]
        [calls]:    _reset_header
        """
        if not asserts(self.config is not None,
                       "self.config must be initialized before calling on_username."):
            return

        self.config.set("Text", "username", value)
        self.config.write()
        self._reset_header(value, self.config.get("Text", "cmd_identifier"))
