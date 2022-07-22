import re
from pylejandria.gui import TextArea, ask, Window, WindowMenu, style
import subprocess
import threading
import json

FILENAME = 'program_run'

tags = [
    'Frame', 'Window', 'Combobox', 'Button', 'TextSpan', 'Entry', 'Label',
    'Tk', 'TextSpan', 'WindowMenu', 'Combobox', 'LabelFrame', 'TextArea'
]

tk_syntax = {
    f"^[ :]*({'|'.join(tags)})$": ('Keyword', (0, 0), {'foreground': '#ff0080'}),
    f": {'|'.join(tags)}": ('Keyword', (0, 0), {'foreground': '#ff0080'}),
    "'.*'": ('String', (0, 0), {'foreground': '#ffff80'}),
    '[0-9]+(\.[0-9]+){0,1}': ('Number', (0, 0), {'foreground': '#cc80ff'}),
    '\{|\}|\[|\]|\(|\)|\|': ('Bracket', (0, 0), {'foreground': '#ff0080'}),
    '(\.){0,1}[a-zA-Z]+:': ('Property', (0, 0), {'foreground': '#00cccc'}),
    '[A-Z]+_[A-Z]+(_[A-Z]+)*': ('Variable', (0, 0), {'foreground': '#0080ff'}),
    '\$[a-z_]+': ('function', (0, 0), {'foreground': '#80ff00'}),
    '(#[a-zA-Z_]+|self)': ('Reference', (0, 0), {'foreground': '#ffff30'})
}

keywords = [
    'from', 'import', 'while ', 'for ', 'if ', 'elif ', 'else',
    'return', 'not ', ' is ', 'match ', 'case', ' as ', 'global '
]

py_syntax = {
    '\+|\*|\-|/|\||\<|\>|=|:=': ('Operators', (0, 0), {'foreground': '#ff0080'}),
    '\(|\)|\{|\}|\[|\]': ('Brackets', (0, 0), {'foreground': '#ff0080'}),
    '|'.join(keywords): ('Keywords', (0, 0), {'foreground': '#ff0080'}),
    '[0-9]+(\.[0-9]+){0,1}': ('Numbers', (0, 0), {'foreground': '#cc40cc'}),
    'def ': ('Def', (0, 0), {'foreground': '#00ffff'}),
    'def [a-zA-Z_]+\(': ('Function', (4, 1), {'foreground': '#80ff40'}),
    '\.[a-zA-Z_]+\(': ('Method', (1, 1), {'foreground': '#00ffff'}),
    '[A-Z_]+,': ('Global1', (0, 1), {'foreground': '#cc40cc'}),
    ', [A-Z]+': ('Global2', (2, 0), {'foreground': '#cc40cc'}),
    ' [A-Z][A-Z]+': ('Global3', (0, 0), {'foreground': '#cc40cc'}),
    '[A-Z_]+ =': ('Global4', (0, 2), {'foreground': '#cc40cc'}),
    'True|False|None': ('Variables', (0, 0), {'foreground': '#cc40cc'}),
    '[a-zA-Z_]+: ': ('Key', (0, 2), {'foreground': '#ff8000'}),
    ' __[a-z]+__ ': ('Dunder1', (1, 1), {'foreground': '#80ffff'}),
    ', __[a-z]+__ ': ('Dunder2', (2, 0), {'foreground': '#80ffff'}),
    ', __[a-z]+__, ': ('Dunder3', (2, 2), {'foreground': '#80ffff'}),
    "f'": ('Fstring', (0, 1), {'foreground': '#00ffff'}),
    "'.*'": ('String', (0, 0), {'foreground': '#ffff80'}),
    'print|input|eval|open': ('Builtin', (0, 0), {'foreground': '#00ffff'}),
    '[A-Z][a-z]+': ('Class', (0, 0), {'foreground': '#00ffff'})
}


def highlight(textarea: ..., syntax: dict):
    lines = textarea.read().split('\n')
    for row, line in enumerate(lines):
        for regex, (name, boundaries, values) in syntax.items():
            for match in re.finditer(regex, line):
                start = f'{row+1}.{match.start()+boundaries[0]}'
                end = f'{row+1}.{match.end()-boundaries[1]}'
                textarea.tag_add(name, start, end)
                textarea.tag_config(name, **values)


def new_files(*e):
    tk_area.clear()
    py_area.clear()


def open_files(*e):
    filenames = ask('openfilenames')
    for filename in filenames:
        with open(filename, 'r') as f:
            if filename.endswith('.tk'):
                tk_area.write(f.read(), clear=True)
                highlight(tk_area, tk_syntax)
            if filename.endswith('.py'):
                py_area.write(f.read(), clear=True)
                highlight(py_area, py_syntax)
            if filename.endswith('.json'):
                style_area.write(f'STYLE = {f.read()}', clear=True)
                highlight(style_area, py_syntax)


def save_files(*e):
    global FILENAME
    if not FILENAME:
        FILENAME = ask('saveasfilename')
        FILENAME = FILENAME.split('.')[0]
    with open(f'{FILENAME}.py', 'w') as f:
        f.write(py_area.read())
    with open(f'{FILENAME}.tk', 'w') as f:
        f.write(tk_area.read())
    with open(f'{FILENAME}.json', 'w') as f:
        style_dict = json.loads(style_area.read().replace('STYLE = ', ''))
        json.dump(style_dict, f, indent=4)


def run_thread():
    subprocess.call(["python", f"./{FILENAME}.py"])


def run(*e):
    with open(f"{FILENAME}.tk", "w") as tk_file:
        file = tk_area.read()
        for match in re.finditer('[\r\n]{2,}', file):
            file = file.replace(match.group(), '\n')
        if file.endswith('\n'):
            file = file[:-1]
        tk_file.write(file)
    with open(f"{FILENAME}.py", "w") as py_file:
        file = py_area.read()
        new_file = 'from tksystem.functions import load\n'
        new_file += 'import sys\n\n'
        new_file += 'sys.dont_write_bytecode = True\n'
        new_file += file
        new_file += style_area.read()
        new_file += "\nif __name__ == '__main__':\n"
        new_file += f"\twindow = load('{FILENAME}.tk', __file__, style_dict=STYLE)\n"
        new_file += '\twindow.mainloop()'
        py_file.write(new_file)

    thread = threading.Thread(target=run_thread)
    thread.start()


menu_dict = {
    'File': {
        'tearoff': False,
        'New': {'accelerator': 'Ctrl+N', 'command': new_files},
        'Open': {'accelerator': 'Ctrl+O', 'command': open_files}
    },
    'Edit': {
        'tearoff': False,
        'Cut': {'accelerator': 'Ctrl+X'},
        'Copy': {'accelerator': 'Ctrl+C'},
        'Paster': {'accelerator': 'Ctrl+V'},
        'separator': {},
        'Undo': {'accelerator': 'Ctrl+Z'},
        'Redo': {'accelerator': 'Ctrl+Y'},
    }
}

style_dict = {
    'text_area': {
        'bg': '#181818',
        'fg': '#ffffff',
        'linefg': '#ffffff',
        'selectbackground': '#404030',
        'selectforeground': '#ffffff',
        'insertbackground': '#ffffff'
    }
}

window = Window()
window['bg'] = '#262626'
window.bind('<Control-o>', open_files)
window.bind('<Control-n>', new_files)
window.bind('<Control-r>', run)
window.bind('<Control-s>', save_files)

menu = WindowMenu(window, menu_dict)

tk_area = TextArea(window, scrollbar=False, width=80)
tk_area.pack(side='left', fill='both', expand=True)
tk_area = style(None, style_dict, widget=tk_area, alias='text_area')
tk_area.bind('<Key>', lambda e: highlight(tk_area, tk_syntax))
tk_area.write('Tk')
tk_area['tabs'] = '32'

py_area = TextArea(window, scrollbar=False, width=80)
py_area.pack(side='left', fill='both', expand=True)
py_area = style(None, style_dict, widget=py_area, alias='text_area')
py_area.bind('<Key>', lambda e: highlight(py_area, py_syntax))
tk_area['tabs'] = '32'

style_area = TextArea(window, scrollbar=False, width=40)
style_area.pack(side='left', fill='y')
style_area = style(None, style_dict, widget=style_area, alias='text_area')
style_area.write('STYLE = {\n\n}')
style_area.bind('<Key>', lambda e: highlight(style_area, py_syntax))
tk_area['tabs'] = '32'

window.mainloop()