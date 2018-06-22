import sys
from stack import CommandStack

import kivy.properties as kp
from kivy.base import EventLoop
from kivy.clock import Clock
from kivy.uix.textinput import TextInput
from kivy.utils import platform


class AdvancedTextInput(TextInput):

    # Additional instance variables:

    history_stack = kp.ObjectProperty(None)

    password_mode = kp.BooleanProperty(False)

    password_cache = kp.StringProperty("")

    protected_len = kp.NumericProperty()

    command_mode = kp.BooleanProperty(True)

    completion_mode = kp.BooleanProperty(False)

    last_row = kp.NumericProperty(0)
    
    last_row_start = kp.NumericProperty(0)

    __events__ = ('on_text_validate', 'on_double_tap', 'on_triple_tap',
                  'on_quad_touch', 'on_tab', 'on_ctrl_c', 'on_stop_completion',
                  'on_space', 'on_reduce_option', 'on_left_option',
                  'on_right_option', 'on_prev_options', 'on_next_options')

    def __init__(self, **kwargs):
        super(AdvancedTextInput, self).__init__(**kwargs)
        self.history_stack = CommandStack()

    def _key_down(self, key, repeat=False):
        displayed_str, internal_str, internal_action, scale = key
        if internal_action is None:
            if self._selection:
                self.delete_selection()
            self.insert_text(displayed_str)
        elif internal_action in ('shift', 'shift_L', 'shift_R'):
            if not self._selection:
                self._selection_from = self._selection_to = self.cursor_index()
                self._selection = True
            self._selection_finished = False
        elif internal_action == 'ctrl_L':
            self._ctrl_l = True
        elif internal_action == 'ctrl_R':
            self._ctrl_r = True
        elif internal_action == 'alt_L':
            self._alt_l = True
        elif internal_action == 'alt_R':
            self._alt_r = True
        elif internal_action.startswith('cursor_'):
            cc, cr = self.cursor
            self.do_cursor_movement(internal_action,
                                    self._ctrl_l or self._ctrl_r,
                                    self._alt_l or self._alt_r)
            if self._selection and not self._selection_finished:
                self._selection_to = self.cursor_index()
                self._update_selection()
            elif not self.completion_mode:
                self.cancel_selection()
        elif self._selection and internal_action in ('del', 'backspace'):
            self.delete_selection()
        elif internal_action == 'del':
            if self._get_cursor_col() != 0:
                # Move cursor one char to the right. If that was successful,
                # do a backspace (effectively deleting char right of cursor)
                cursor = self.cursor
                self.do_cursor_movement('cursor_right')
                if cursor != self.cursor:
                    self.do_backspace(mode='del')
        elif internal_action == 'backspace':
            if self.password_mode:
                self.password_cache = self.password_cache[:-1]
            if self._get_cursor_col() > self.protected_len:
                self.do_backspace()
        elif internal_action == 'enter':
            if not self.readonly:
                self.dispatch('on_text_validate')
        elif internal_action == 'escape':
            self.focus = False
        if internal_action != 'escape':
            # self._recalc_size()
            pass

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        # Keycodes on OS X:
        ctrl, cmd = 64, 1024
        key, key_str = keycode
        win = EventLoop.window

        # cache the result
        _is_osx = sys.platform == 'darwin'

        # This allows *either* ctrl *or* cmd, but not both.
        is_shortcut = (modifiers == ['ctrl'] or (
            _is_osx and modifiers == ['meta']))
        is_interesting_key = key in (list(self.interesting_keys.keys()) + [27])

        if not self.write_tab and super(AdvancedTextInput,
                                        self).keyboard_on_key_down(window, keycode, text, modifiers):
            return True

        ### changes start here
        if self.completion_mode\
                and key not in (9, 275, 276, 280, 281)\
                and not text:
            self.dispatch('on_stop_completion')
        ### changes end here

        if not self._editable and key != 282:
            # duplicated but faster testing for non-editable keys
            if text and not is_interesting_key:
                if is_shortcut and key == ord('c'):
                    ### changes start here
                    self.dispatch("on_ctrl_c")
                elif is_shortcut and key == ord('a'):
                    self.select_all()
            elif key == 27:
                self.focus = False
            ### changes start here
            #     backspace   delete          _selection is True
            elif (key == 8 or key == 127) and self._selection:
                self.delete_lastchar()
            ### changes end here
            return True

        if text and not is_interesting_key:

            self._hide_handles(win)
            self._hide_cut_copy_paste(win)
            win.remove_widget(self._handle_middle)

            # check for command modes
            # we use \x01INFO\x02 to get info from IME on mobiles
            # pygame seems to pass \x01 as the unicode for ctrl+a
            # checking for modifiers ensures conflict resolution.

            first_char = ord(text[0])
            if not modifiers and first_char == 1:
                self._command_mode = True
                self._command = ''
            if not modifiers and first_char == 2:
                self._command_mode = False
                self._command = self._command[1:]

            if self._command_mode:
                self._command += text
                return

            _command = self._command
            if _command and first_char == 2:
                from_undo = True
                _command, data = _command.split(':')
                self._command = ''
                if self._selection:
                    self.delete_selection()
                if _command == 'DEL':
                    count = int(data)
                    if not count:
                        self.delete_selection(from_undo=True)
                    end = self.cursor_index()
                    self._selection_from = max(end - count, 0)
                    self._selection_to = end
                    self._selection = True
                    self.delete_selection(from_undo=True)
                    return
                elif _command == 'INSERT':
                    self.insert_text(data, from_undo)
                elif _command == 'INSERTN':
                    from_undo = False
                    self.insert_text(data, from_undo)
                elif _command == 'SELWORD':
                    self.dispatch('on_double_tap')
                elif _command == 'SEL':
                    if data == '0':
                        Clock.schedule_once(lambda dt: self.cancel_selection())
                elif _command == 'CURCOL':
                    self.cursor = int(data), self.cursor_row
                return

            if is_shortcut:
                if key == ord('x'):  # cut selection
                    ### changes start here
                    pass
                    ### changes end here
                elif key == ord('c'):  # copy selection
                    ### changes start here
                    self.dispatch("on_ctrl_c")
                    ### changes start here
                elif key == ord('v'):  # paste selection
                    self.paste()
                elif key == ord('a'):  # select all
                    self.select_all()
                elif key == ord('z'):  # undo
                    self.do_undo()
                elif key == ord('r'):  # redo
                    self.do_redo()
            else:
                if EventLoop.window.__class__.__module__ == \
                        'kivy.core.window.window_sdl2':
                    if not (text == ' ' and platform == 'android'):
                        return
                if self._selection:
                    self.delete_selection()
                self.insert_text(text)
            # self._recalc_size()
            return

        if is_interesting_key:
            self._hide_cut_copy_paste(win)
            self._hide_handles(win)

        if key == 27:  # escape
            self.focus = False
            return True
        elif key == 9:  # tab
            if not self.password_mode:
                self.dispatch('on_tab')
            return True

        k = self.interesting_keys.get(key)
        if k:
            key = (None, None, k, 1)
            self._key_down(key)

    def delete_selection(self, from_undo=False):
        '''Delete the current text selection (if any).
        '''
        if self.readonly:
            return
        ### changes start from here

        # If the selection includes protected parts, cancel selection.
        index = 0 if self.last_row < 1 else self.last_row_start

        ### when user selected both protected texts and the command
        if self.selection_from < index + self.protected_len:
            self.delete_lastchar()
            return

        ### changes end here
        self._hide_handles(EventLoop.window)
        scrl_x = self.scroll_x
        scrl_y = self.scroll_y
        cc, cr = self.cursor
        if not self._selection:
            return
        v = self._get_text(encode=False)
        a, b = self._selection_from, self._selection_to
        if a > b:
            a, b = b, a
        self.cursor = cursor = self.get_cursor_from_index(a)
        start = cursor
        finish = self.get_cursor_from_index(b)
        cur_line = self._lines[start[1]][:start[0]] +\
            self._lines[finish[1]][finish[0]:]
        lines, lineflags = self._split_smart(cur_line)
        len_lines = len(lines)
        if start[1] == finish[1]:
            self._set_line_text(start[1], cur_line)
        else:
            self._refresh_text_from_property('del', start[1], finish[1], lines,
                                             lineflags, len_lines)
        self.scroll_x = scrl_x
        self.scroll_y = scrl_y
        # handle undo and redo for delete selection
        self._set_unredo_delsel(a, b, v[a:b], from_undo)
        self.cancel_selection()

    def do_cursor_movement(self, action, control=False, alt=False):
        '''Move the cursor relative to it's current position.
        Action can be one of :

            - cursor_left: move the cursor to the left
            - cursor_right: move the cursor to the right
            - cursor_up: display and select the previous command
            - cursor_down: display and select the next command
            - cursor_home: move the cursor at the start of the current line
            - cursor_end: move the cursor at the end of current line
            - cursor_pgup: move one "page" before
            - cursor_pgdown: move one "page" after

        In addition, the behavior of certain actions can be modified:

            - control + cursor_left: move the cursor one word to the left
            - control + cursor_right: move the cursor one word to the right
            - control + cursor_up: scroll up one line
            - control + cursor_down: scroll down one line
            - control + cursor_home: go to beginning of text
            - control + cursor_end: go to end of text
            - alt + cursor_up: shift line(s) up
            - alt + cursor_down: shift line(s) down

        .. versionchanged:: 1.9.1

        '''
        if not self._lines:
            return
        pgmove_speed = int(self.height /
                           (self.line_height + self.line_spacing) - 1)
        col, row = self.cursor
        if action == 'cursor_up':
            # enable history search when on command_mode
            if self.command_mode:
                self.history_stack.step_back()
                col, row = self.display_command(self.history_stack.peak())
        elif action == 'cursor_down':
            # enable history search when on command_mode
            if self.command_mode:
                self.history_stack.step_forward()
                col, row = self.display_command(self.history_stack.peak())
        elif action == 'cursor_left':
            ### changes in the next line
            if not self.password_mode and control:
                col, row = self._move_cursor_word_left()
            ### changes in the next two lines
            elif self.completion_mode:
                self.dispatch("on_left_option")
                col, row = self.cursor
            elif self._get_cursor_col() > self.protected_len:
                col, row = col - 1, row
        elif action == 'cursor_right':
            ### changes in the next line
            if not self.password_mode and control:
                col, row = self._move_cursor_word_right()
            ### changes in the next two lines
            elif self.completion_mode:
                self.dispatch("on_right_option")
                col, row = self.cursor
            else:
                if col == len(self._lines[row]):
                    if row < self.last_row:
                        col = 0
                        row += 1
                else:
                    col, row = col + 1, row
        elif action == 'cursor_home':
            col = 0
            if control:
                row = 0
        elif action == 'cursor_end':
            if control:
                row = self.last_row
            col = len(self._lines[row])
        elif action == 'cursor_pgup':
            ### changes start here
            if self.completion_mode:
                self.dispatch("on_prev_options")
            else:
                row = max(0, row - pgmove_speed)
                col = min(len(self._lines[row]), col)
            ### changes end here
        elif action == 'cursor_pgdown':
            ### changes start here
            if self.completion_mode:
                self.dispatch("on_next_options")
            else:
                row = min(row + pgmove_speed, self.last_row)
                col = min(len(self._lines[row]), col)
            ### changes end here
        self.cursor = (col, row)
    
    def on_touch_down(self, touch):
        if self.disabled:
            return

        touch_pos = touch.pos
        if not self.collide_point(*touch_pos):
            return False
        if super(AdvancedTextInput, self).on_touch_down(touch):
            return True

        if self.focus:
            self._trigger_cursor_reset()

        # Check for scroll wheel
        if 'button' in touch.profile and touch.button.startswith('scroll'):
            scroll_type = touch.button[6:]
            if scroll_type == 'down':
                if self.multiline:
                    if self.scroll_y <= 0:
                        return
                    self.scroll_y -= self.line_height
                else:
                    if self.scroll_x <= 0:
                        return
                    self.scroll_x -= self.line_height
            if scroll_type == 'up':
                if self.multiline:
                    ### changes in the next two lines
                    if (self.scroll_y + self.line_height - 1 >=
                            (self.last_row) * self.line_height):
                        return
                    self.scroll_y += self.line_height
                else:
                    if (self.scroll_x + self.width >=
                            self._lines_rects[-1].texture.size[0]):
                        return
                    self.scroll_x += self.line_height

        touch.grab(self)
        self._touch_count += 1
        if touch.is_double_tap:
            self.dispatch('on_double_tap')
        if touch.is_triple_tap:
            self.dispatch('on_triple_tap')
        if self._touch_count == 4:
            self.dispatch('on_quad_touch')

        self._hide_cut_copy_paste(EventLoop.window)
        # schedule long touch for paste
        self._long_touch_pos = touch.pos
        self._long_touch_ev = Clock.schedule_once(self.long_touch, .5)

        self.cursor = self.get_cursor_from_xy(*touch_pos)
        if not self._selection_touch:
            self.cancel_selection()
            self._selection_touch = touch
            self._selection_from = self._selection_to = self.cursor_index()
            self._update_selection()
        
        ### added one line here
        self.cancel_selection()
        ### deleted four lines here

        return False

    def on_cursor(self, instance, value):
        # When the cursor is moved, reset cursor blinking to keep it showing,
        # and update all the graphics.
        if self.focus:
            self._trigger_cursor_reset()
            if self._get_cursor_row() != self.last_row or \
                    self._get_cursor_col() < self.protected_len:
                # import pdb; pdb.set_trace()
                self._editable = False
            else:
                self._editable = True
        self._trigger_update_graphics()

    def keyboard_on_textinput(self, window, text):
        ### changes start here
        if self._selection:
            self.cancel_selection()
        if not self._editable:
            self.do_cursor_movement("cursor_end", control=True)
        if self.password_mode:
            self.password_cache += text
        else:
            self.insert_text(text, False)
        if text == " ":
            self.dispatch("on_space")
        elif self.completion_mode:
            self.dispatch("on_reduce_option")
        ### changes end here
        return

    def select_all(self):
        ''' Select all of the text displayed in this TextInput.

        .. versionadded:: 1.4.0
        '''
        ### changes start here
        text_end = len(self.text)
        line_start = text_end - (len(self._lines[-1]) - self.protected_len)
        if self._selection and self.selection_from == line_start\
                and self.selection_to == text_end or \
                len(self._lines[-1]) == self.protected_len:
            self.select_text(0, text_end)
        else:
            self.select_text(line_start, text_end)
        ### changes end here

    ### custom functions:

    def display_command(self, text):
        self.cancel_selection()
        index = 0 if self.last_row < 1 else self.last_row_start
        start = index + self.protected_len
        end = len(self.text)
        self.select_text(start, end)
        self.delete_selection()
        self.insert_text(text)
        col, row = self.cursor
        return len(self._lines[row]), row

    def on_password_mode(self, instance, value):
        if not value:
            self.password_cache = ''

    def on_tab(self):
        pass

    def on_ctrl_c(self):
        pass
    
    def on_left_option(self):
        pass
    
    def on_next_options(self):
        pass
    
    def on_prev_options(self):
        pass

    def on_stop_completion(self):
        pass

    def on_space(self):
        pass

    def on_reduce_option(self):
        pass

    def on_right_option(self):
        pass
    
    def delete_lastchar(self):
        self.cancel_selection()
        self.do_cursor_movement("cursor_end", control=True)
        if self._get_cursor_col() > self.protected_len:
            self.do_backspace()
