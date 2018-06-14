import kivy.properties as kp
from kivy.app import App
from kivy.lang import Builder
from kivy.uix.settings import Settings, SettingsWithSidebar
from kivy.uix.widget import Widget
from kivy.config import ConfigParser

from advancedtextinput import AdvancedTextInput
from controller import SiraController

###
def overrides(interface_class):
    def overrider(method):
        assert(method.__name__ in dir(interface_class))
        return method
    return overrider

class SiraApp(App):

    """The application class for Sira application, working as a view.

    extends:
        kivy.app.App

    Instance Variables:
        Class-scope Variables:
            header -- kivy.properties.StringPorperty (default None)
            info -- kivy.properties.ListProperty (default [])
            [TODO] option -- kivy.properties.ListProperty (default [])
            protected_text -- kivy.properties.StringPorperty (default None)
            username -- kivy.properties.StringPorperty (default None)

        Method-established Variables:
            commandText -- advancedtextinput.AdvancedTextInput (default None)
            config_func_dict -- dict((str, str) : callable)

    Public Methods:
        Overrided from kivy.app.App:
            build(self) -> kivy.uix.widget.Widget()
            build_config(self, config) -> None
            build_settings(self, kivy.uix.settings.Settings()) -> None
            on_config_change(self, config, section, key, value) -> None

        Original:
            on_clear(self) -> None
            print_header(self) -> None
            set_command_mode(self, bool) -> None
            set_controller(self, controller.SiraController()) -> None
            set_pwd_mode(self) -> None


    Private Methods:
        __init__(self, **kwargs) -> None
        _on_cmd_idf(self, str) -> None
        _on_font_size(self, str) -> None
        [TODO] _on_tab(self, kivy.uix.widget.Widget()) -> None
        _on_command(self, kivy.uix.widget.Widget()) -> None
        _stop_interaction(self, kivy.uix.widget.Widget()) -> None
        _reset_header(self, str, str) -> None

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
            _reset_header() to preserve [convention #1.1].

    Property Driven Methods:
        on_info(self, kivy.uix.widget.Widget(), list()) -> None
        on_option(self, kivy.uix.widget.Widget(), list()) -> None
        on_username(self, kivy.uix.widget.Widget(), str) -> None

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

    # option = kp.ListProperty([])

    protected_text = kp.StringProperty(None)
    """Kivy string property to store the protected_text of the current
    command line.

    [convention #3]: {
        (self.protected_text = self.commandText._lines[-1])         #3.1
    }

    [callback]: self.commandText.protected_len (from res/sira.kv)
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
            ("Text", "cmd_identifier") : self._on_cmd_idf,
            ("Text", "font_size") : self._on_font_size
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
        assert isinstance(self.config, ConfigParser), """
                self.config is not initialized.
            """

        self.settings_cls = SettingsWithSidebar
        self.username = self.config.get("Text", "username")
        self._reset_header(self.username,
            self.config.get("Text", "cmd_identifier"))
        self.protected_text = self.header
        self.commandText = Builder.load_file("res/sira.kv")
        return self.commandText

    @overrides(App)
    def build_config(self, config: ConfigParser) -> None:
        """Builder of self.config from src/sira.ini.

        [ensures]:  self.config is not None
                    [self.config has all attributes in its source file]
                    [At least, the following attributes exist:
                        "Text", "user_name"
                        "Text", "cmd_identifier"
                        "Text", "font_size"
                    ]
        """
        config.read("src/sira.ini")

    @overrides(App)
    def build_settings(self, settings: Settings) -> None:
        """Builds and adds custom setting pannels to original settings,
        called when the user open settings for the first time.
        
        [requires]: isinstance(self.config, kivy.config.Config)
                    [see [ensures] of build_config]
        """
        assert isinstance(self.config, ConfigParser), """
                self.config is not initialized.
            """
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
            assert (section, key) in self.config_func_dict.keys(), """
                ({}, {}) is not a key pair in self.config_func_dict
            """.format(section, key)
            self.config_func_dict[(section, key)](value)

    def on_clear(self) -> None:
        """Public function to clear the screen. This methods essentially
        scrolls all historical texts above the window.
        """
        instance = self.commandText
        instance.scroll_y = (len(instance._lines) - 1) * instance.line_height

    def print_header(self) -> None:
        """Public function to print self.header in self.commandText.

        [requires]: self.header is not None
                    self.commandText is not None
        [ensures]:  [self.header displays as the last part in self.commandText]
                    self.protected_text = self.header
        [calls]:    [reset self.commandText.protected_len]
        """
        assert self.header is not None, """
            self.header must be initialized before calling print_header.
        """
        assert self.commandText is not None, """
            self.commandText must be initialized before calling print_header.
        """

        self.commandText.insert_text("\n" + self.header)
        self.protected_text = self.header

    def set_pwd_mode(self) -> None:
        """Public function to set self.commandText.password_mode to True.

        [ensures]:  self.commandText.password_mode = True
        """
        self.commandText.password_mode = True

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

    def _on_cmd_idf(self, value: str) -> None:
        """Privated function fired when cmd_identifier is changed through
        self.config.

        [ensures]:  reset self.header to preserve [convention #1.1]
        [calls]:    _reset_header
        """
        self._reset_header(self.username, value)

    def _on_font_size(self, value: str) -> None:
        """Privated function fired when font_size is changed through
        self.config.

        [ensures]:  self.commandText.font_size = int(value)
        """
        self.commandText.font_size = int(value)

    def _on_tab(self, instance):
        """TODO
        """
        pass

    def _on_command(self, instance: AdvancedTextInput) -> True:
        """"Privated function fired when self.commandText.on_text_validate is
        called, in other words, when users hit the 'enter' key. This property
        is established by res/sira.kv.

        [ensures]:  len(instance._lines) > 0
                    instance.protected_len <= len(instance._lines[-1])
                    instance.password_mode = False
                    instance.history_stack.traversal =
                        instance.history_stack.traversal_dummy
        [calls]:    instance.history_stack.reset_traversal
                    self.controller.processInput
        """
        string = instance._lines[-1][instance.protected_len:]
        if instance.password_mode:
            string = instance.password_cache
            instance.password_mode = False
        elif instance.command_mode:
            instance.history_stack.push(string)
        instance.history_stack.reset_traversal()
        self.controller.processInput(instance, string)
        return True

    def _reset_header(self, username: str, identifier: str) -> None:
        """Private funciton to reset self.header based on username and
        identifier to preserve [convention #1.1]

        [ensures]:  [convention #1.1]
        """
        self.header = username + identifier

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

    def on_info(self, instance: AdvancedTextInput, info: list) -> None:
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
        self.commandText.do_cursor_movement("cursor_end", control=True)
        self.protected_text = info[-1]
        for s in info:
            assert isinstance(s, str), """
                (for line in self.info: isinstance(line, str)).
            """
            self.commandText.insert_text("\n" + str(s))
        self.info = []

    def on_option(self, instance, info):
        """TODO
        """
        pass

    def on_username(self, instance: AdvancedTextInput, value: str) -> None:
        """Property driven function, fired when username is changed. This
        function writes the new value in self.config and its corresponding
        config files.

        [requires]: self.config is not None
                    [convention #4.1] (unchecked)
        [ensure]:   self.config.get("Text", "username") = value
                    [convention #1.1]
        [calls]:    _reset_header
        """
        assert self.config is not None, """
            self.config must be initialized before calling on_username.
        """

        self.config.set("Text", "username", value)
        self.config.write()
        self._reset_header(value, self.config.get("Text", "cmd_identifier"))
