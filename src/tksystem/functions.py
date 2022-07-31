from tksystem.parser import run
import pylejandria
import tkinter as tk
from tkinter import ttk


def import_widget(name, module):
    for source in (module, pylejandria.gui, tk, ttk):
        if widget := source.__dict__.get(name):
            return widget
    raise AttributeError(f'Not widget {name!a} founded.')


def parse_file(text):
    start_index = 0
    widget_properties = []
    key_points = [line for line in text if ':' not in line] + [None]
    for point_a, point_b in pylejandria.tools.pair(key_points, 2):
        widget_properties.append({})
        index_a = text.index(point_a, start_index)
        index_b = text.index(point_b, start_index) if point_b else len(text)
        widget_properties[-1]['widget'] = text[index_a].strip()
        widget_properties[-1]['indent'] = text[index_a].count('\t')
        for index in range(index_a+1, index_b):
            line = text[index].strip()
            key, value = line.split(':', maxsplit=1)
            widget_properties[-1][key] = value
        start_index = index_b
    return widget_properties


def assign_parent(widget_a, widget_b, indent_a):
    indent_b = widget_b['indent']
    parent = widget_a
    
    if indent_a < indent_b:
        return parent
    if indent_a == indent_b:
        return parent.master
    for _ in range(indent_b - indent_a):
        parent = parent.master
    return parent.master


def clean(text):
    lines = text.split('\n')
    clean_lines = []
    for line in lines:
        if not line: continue
        if all([char in ('\t', ' ') for char in line]): continue
        clean_lines.append(line)
    return clean_lines


def place_widget(widget, info):
    if not any([
        info.get('.pack'),
        info.get('.grid'),
        info.get('.place'),
    ]) and getattr(widget, 'pack', None):
        widget.pack()


def make_error(error, line):
    return error.as_string(line)


def load(tk_filename, file):
    module = pylejandria.tools.get_module(file) if file is not None else None
    with open(tk_filename, 'r') as f:
        tk_text = f.read()
    
    clean_text = clean(tk_text)
    widget_properties = parse_file(clean_text)
    main = None
    line_count = 1

    for index in range(len(widget_properties)):
        line_count += 1
        widget_a = widget_properties[index]
        widget_b = widget_properties[index + 1] if index + 1 < len(widget_properties) else None
        indent_a = widget_a.pop('indent')
        widget_name = widget_a.pop('widget')
        widget_class = import_widget(widget_name, module)

        widget = widget_class() if main is None else widget_class(widget_a.pop('parent'))

        id_widgets = {}

        place_widget(widget, widget_a)

        for key, str_value in widget_a.items():
            value, error = run('<TkSystem>', str_value, {'self': widget} | id_widgets)
            if error: return None, make_error(error, line_count)
            value = value.to_python()
            if key == 'id': id_widgets[value] = widget
            elif key.startswith('.'):
                method = getattr(widget, key[1:])
                if isinstance(value, list): method(*value)
                elif isinstance(value, dict): method(**value)
                else: method(value)
            else: widget[key] = value
            line_count += 1
        
        if main is None:
            main = widget
        
        if widget_b is not None:
            parent = assign_parent(widget, widget_b, indent_a)
            widget_b['parent'] = parent

    return main, None

if __name__ == '__main__':
    window, error = load('c:/users/angel/desktop/tksystem/project.tk', __file__)
    if error: print(error)
    else: window.mainloop()