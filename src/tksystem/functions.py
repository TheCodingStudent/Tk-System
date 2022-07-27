from typing import Any
import pylejandria
import re
import tkinter as tk
from tkinter import ttk


def get_chunk(a: str, b: str, lines: list[str]) -> tuple[list[str], list[str]]:
    """
    Extract the lines between widgets based on the name.
    Params:
        a: first widget.
        b: second widget.
        lines: lines of the source file.
    Returns:
        the remaining lines to not repeat and the stripped lines between
        widgets, also the indent level.
    """
    if b is None:
        return [], [line.strip() for line in lines], a.count('    ')
    start = lines.index(a)
    end = lines.index(b, start+1)
    return (
        lines[end:], [line.strip() for line in lines[start:end]],
        a.count('    ')
    )


def find_attribute(name: str, sources: list[Any]) -> Any:
    """
    Returns the attribute from the given sources.
    Params:
        name: name of the attribute to return.
        sources: list of sources to search from.
    Returns:
        Any: the wanted attribute in case it exists. Else raises an error.
    """
    for source in sources:
        try:
            return getattr(source, name)
        except AttributeError:
            continue
    raise AttributeError(f'Attribute {name!s} not found')


def widget_info(chunk: list[str], indent: int) -> dict:
    """
    Gets a list of lines of a widget and returns a dictionary with its
    properties.
    Params:
        chunk: list of strings of a widget.
    Returns:
        widget: dict with all the properties extracted from the chunk.
    """
    widget = {}
    widget['widget'] = chunk.pop(0)
    widget['indent'] = indent

    for item in chunk:
        key, value = item.split(': ', maxsplit=1)
        if key in ('execute', ):
            if widget.get(key):
                widget[key].append(value)
            else:
                widget[key] = [value]
        else:
            try:
                widget[key] = eval(value)
            except:
                widget[key] = value
    return widget


def get_widgets(
    lines: list[str], names: list[str]
) -> list[dict | None, str | None]:
    """
    Evaluate the lines from the source file, checks between each of them, gets
    a chunk and then its info.
    Params:
        lines: lines from the source file.
        names: names of the widgets.
    Returns:
        widgets: a list with tuples containing a dictionary with the widget
        properties and its id in case it haves.
    """
    widgets = []
    for a, b in pylejandria.tools.pair(names + [None], 2):
        lines, chunk, indent = get_chunk(a, b, lines)
        widget = widget_info(chunk, indent)
        widgets.append((widget, widget.get('id')))
    widgets.append((None, None))
    return widgets


def place_widget(widget: Any, info: dict) -> None:
    """
    Manages the place method of the widget based on its info.
    Params:
        widget: widget to place.
        info: info of the widget.
    Returns:
        None
    """
    if info.get('.pack'):
        widget.pack(**info.pop('.pack'))
    elif info.get('.place'):
        widget.place(**info.pop('.place'))
    elif info.get('.grid'):
        widget.grid(**info.pop('.grid'))
    else:
        try:
            widget.pack()
        except AttributeError:
            pass


def widget_args(info: dict):
    """
    Extracts main arguments from the info of widget.
    Params:
        info: dictionary of properties of a widget.
    """
    args = []
    if info.get('parent'):
        args.append(info.pop('parent'))
    return args


def get_widget(widgets: dict, widget_id: str) -> Any:
    """
    Returns a widget based on its id, if it doesnt exists then raises an error.
    Params:
        widgets: dictionary of widgets with id as key.
        widget_id: id of the widget to return.
    Returns:
        widget: widget from the widgets dictionary.
    Raises:
        An AttributeError with a message to easily find which widget was not
        founded.
    """
    if widget := widgets.get(widget_id):
        return widget
    raise AttributeError(f'widget {widget_id!s} not found')


def get_variables(expression: str) -> list[str, list]:
    """
    Checks if the expression follows the following format, if so then returns
    the parsed expression and the arguments. The arguments are not evaluated.
    Format:
        - (arg1 | arg2 | ...)
    Params:
        expression: string expression to parse.
    Returns:
        expression: parsed expression.
        str_args: arguments from the expression.
    """
    if args := re.search('\(.*\)', expression):
        args = args.group()
        expression = expression.replace(args, '')
    str_args = [] if args is None else args[1:-1].split(' | ')
    return expression, str_args


def get_property(expression: str, widget: tk.Widget, widgets: dict) -> Any:
    """
    checks if the expression follows the following format, if so then returns
    the parsed expression and the proper value.
    Format:
        - self: refers to the widget itself.
        - #name: refers to a widget with id name.
        - [property]: returns the given property of the widget.
    Examples:
        - self.master
        - #topleft_frame.label['text']
    Params:
        expression: string expression to parse.
        widget: current widget, in case its referenced.
        widgets: dict of widgets, in case any is referenced.
    Returns:
        any: the corresponding value based on the expression.
    """
    property_ = None
    if args := re.search("\['.+'\]", expression):
        args = args.group()
        expression = expression.replace(args, '')
        property_ = eval(args[1:-1])
    if expression.startswith('#'):
        expression = expression.replace('#', '')
        widget_property = widgets.get(expression)
        if property_ is None:
            return widget_property
        return widget_property[property_]
    elif expression.startswith('self'):
        return widget[property_]
    else:
        widget_property = getattr(widget, expression)
        return widget_property[property_]


def parse_property(
    expression: str, widget: tk.Widget, widgets: dict, module: Any
) -> Any:
    """
    Checks if the expression follows the following format, if so then returns
    the corresponding property.
    Format:
        - $function_name: single function.
        - $function_name(arg1 | arg2 | ...): function with parameters.
        - self | #id: reference to itself or a widget with id.
        - (self | #id).property: refers to a property of the first item.
    Params:
        expression: string expression to parse.
        widget: current widget, in case its referenced.
        widgets: dict of widgets, in case any is referenced.
        module: loaded source file to be referenced.
    Returns:
        Any: the corresponding value.
    """
    if str(expression).startswith('$'):
        expression = expression.replace('$', '')
        args = []
        if str_args := re.search("\(.*\)", expression):
            expression, str_args = get_variables(expression)
            args = [
                parse_property(arg, widget, widgets, module)
                for arg in str_args
            ]
        func = getattr(module, expression)
        return lambda *e: func(*args)
    elif re.match("(self|#.+)(\.[a-z]*)*(\['[a-z]*'\]){0,1}", str(expression)):
        result = None
        for method in expression.split('.'):
            if method == 'self':
                result = widget
            elif method.startswith('#') or re.search("\['.+'\]", method):
                result = get_property(method, widget, widgets)
                return result if result else method
            else:
                if str_args := re.search("\(.*\)", method):
                    method, str_args = get_variables(method)
                    args = [
                        parse_property(arg, widget, widgets, module)
                        for arg in str_args
                    ]
                    func = getattr(result, method)
                    return lambda *e: func(*args)
                result = getattr(result, method)
        return result
    elif str_args := re.match("\(.*\)", str(expression)):
        expression, str_args = get_variables(expression)
        return [
            parse_property(arg, widget, widgets, module) for arg in str_args
        ]
    try:
        return eval(expression)
    except:
        return expression


def assign_parent(widget: Any, info1: dict, info2: dict) -> tk.Widget | None:
    """
    Assigns parent to the widget based on the indentation.
    Params:
        widget: current widget, is used to get the parent or be the parent.
        info1: dictionary of the current widget.
        info2: dictionary of the next widget.
    Returns:
        parent: parent widget of the current widget.
        Or None.
    """
    parent = widget
    indent1 = info1.get('indent')
    indent2 = info2.get('indent') if info2 else None
    if indent2 is None:
        return None
    if indent1 == indent2:
        parent = parent.master
    elif indent1 > indent2:
        for _ in range(indent1 - indent2 + 1):
            parent = parent.master
    return parent


def load(
    filename: str, file: str, parent: tk.Widget | None=None,
    style_dict: dict | None={}, filetext: str | None=None
) -> tk.Widget:
    """
    Loads a file with extension *.tk and builds all the widgets, the idea is
    to have a setup more or less like QML, a cascade of widgets, is meant to
    simple UI.
    Params:
        filename: path of the *.tk file.
        file: path of the source, to load functions and classes.
        parent: optional parent, in case the loaded widget is not a window.
        style_dict: optional dictionary with style based on alias.
        filetext: string with the text in case there is no file.
    Returns:
        tk.Widget: the builded widget from the given file.
    """
    if filename is not None:
        with open(filename, 'r') as f:
            lines = f.read().split('\n')
    else:
        lines = filetext.split('\n')

    widget_names = [line for line in lines if ':' not in line]
    module = pylejandria.tools.get_module(file) if file is not None else None
    widgets = get_widgets(lines, widget_names)
    window = None
    built = {}

    for info1, info2 in pylejandria.tools.pair(widgets, 2, index=0):
        if parent is not None:
            info1['parent'] = parent
            parent = None
        widget = find_attribute(
            info1.pop('widget'), (module, tk, tk.ttk, pylejandria.gui)
        )
        widget_arguments = widget_args(info1)
        widget = widget(*widget_arguments)
        if alias := info1.get('alias'):
            widget = pylejandria.gui.style(None, style_dict, alias=alias, widget=widget)
        if id_ := info1.get('id'):
            built[id_] = widget
        if window is None:
            window = widget
        place_widget(widget, info1)

        for key, value in info1.items():
            if key in ('indent', 'id', 'alias'):
                continue
            elif key == 'execute':
                for func_value in value: 
                    if func := parse_property(func_value, widget, built, module):
                        func()
                continue
            property_ = parse_property(value, widget, built, module)
            if key.startswith('.'):
                func = getattr(widget, key.replace('.', ''))
                if isinstance(property_, (list, tuple)):
                    func(*property_)
                else:
                    func(property_)
            else:
                try:
                    widget[key] = getattr(module, str(property_))
                except AttributeError:
                    try:
                        widget[key] = property_
                    except tk.TclError:
                        print(f'invalid {key!a} property')

        if parent := assign_parent(widget, info1, info2):
            info2['parent'] = parent

    if style_config := style_dict.get('style_config'):
        style = ttk.Style(window)
        for widget, config in style_config.items():
            style.configure(widget, **config)

    return window
