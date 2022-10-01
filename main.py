# Import modules
import json
import os
from pylejandria.gui import Window, WindowMenu, TextArea, Container, ask
import re
from tksystem.reloader import run_with_reloader
from tksystem.functions import parse_file, clean
import subprocess
import threading
import tkinter as tk


class TextFrame(tk.Frame):
    def __init__(self, master: tk.Widget, title: str):
        super().__init__(master)
        ##### Frame properties #####
        self['bg'] = '#181818'

        ##### Title properties #####
        self.title = tk.Label(self, text=title)
        self.title.pack(side='top', fill='x')
        self.title['bg'] = '#181818'
        self.title['fg'] = 'white'

        ##### Text properties #####
        self.text = TextArea(self, width=0)
        self.text['insertbackground'] = 'white'
        self.text['selectbackground'] = '#404030'
        self.text.pack(side='top', expand=True, fill='both')
        self.text['bg'] = '#181818'
        self.text['fg'] = 'white'
        self.text['linefg'] = '#808080'


def load_template(widget: str) -> None:
    index = tk_area.text.text.index('insert')
    row, tabs = map(lambda x: int(x), index.split('.'))
    with open(f'templates.txt', 'r') as f:
        clean_text = clean(f.read())
        widgets = parse_file(clean_text)
        for widget_dict in widgets:
            if widget_dict['widget'] == widget:
                break 
        
        for key, value in widget_dict.items():
            if key in ('indent', ):
                continue
            elif key == 'widget':
                tk_area.text.write(f'{value}\n')
            else:
                tk_area.text.write('\t'*tabs + f'\t{key}: {value}\n')
        tk_area.text.write('\t'*(tabs+1))
    highlight()


def new_files(*e):
    style_area.text.write('STYLE = {\n\n}', clear=True)
    window.title(f'TkSystem 2.0.0')
    highlight()


def open_files(*e):
    directory = ask('directory')
    if os.path.exists(f'{directory}/project.tk'):
        with open(f'{directory}/project.tk', 'r') as f:
            tk_area.text.write(f.read().strip(), clear=True)
    if os.path.exists(f'{directory}/project.py'):
        with open(f'{directory}/project.py', 'r') as f:
            py_area.text.write(f.read().strip(), clear=True)
    if os.path.exists(f'{directory}/project.json'):
        with open(f'{directory}/project.json', 'r') as f:
            text = f'STYLE = {f.read().strip()}'
            style_area.text.write(text, clear=True)
    window.title(f'TkSystem 2.0.0 {directory}')
    highlight()


def save_files(*e, name='c:/users/angel/desktop/compress') -> None:
    with open(f'{name}/project.tk', 'w') as f:
        f.write(tk_area.text.read().strip())
    with open(f'{name}/project.py', 'w') as f:
        f.write(py_area.text.read().strip())
    with open(f'{name}/project.json', 'w') as f:
        style_dict = json.loads(style_area.text.read().replace('STYLE = ', ''))
        json.dump(style_dict, f, indent=4)
    window.title(f'TkSystem 2.0.0 {name}/TkSystem')


##### Window menu #####
MENU = {
    'File': {
        'tearoff': False,
        'New Project': {'accelerator': 'Ctrl+N', 'command': new_files},
        'Open Project': {'accelerator': 'Ctrl+O', 'command': open_files},
        'separator': {},
        'Save Project': {'accelerator': 'Ctrl+S', 'command': save_files},
        'separator': {},
        'Run': {'accelerator': 'Ctrl+R'}
    },
    'View': {
        'tearoff': False,
        'Tk File': {
            'accelerator': 'Ctrl+1', 'command': lambda: load_frame('tk_area')
        },
        'Python File': {
            'accelerator': 'Ctrl+2', 'command': lambda: load_frame('py_area')
        },
        'JSON File': {
            'accelerator': 'Ctrl+3',
            'command': lambda: load_frame('style_area')
        },
        'Add template': {
            'accelerator': 'Ctrl+4',
            'command': lambda: load_frame('template_area')
        }
    },
    'Templates': {
        'tearoff': False
    }
}

with open('templates.txt', 'r') as f:
    clean_text = clean(f.read())
    widgets = parse_file(clean_text)
    for widget in widgets:
        name = widget['widget']
        MENU['Templates'][name] = {'command': eval(f'lambda: load_template("{name}")')}

##### Tk and Python files syntax with regex #####
SYNTAX = {
    'tk_area': {
        '(\'|")#[0-9a-f]{6}(\'|")': ('Color', (1, 1), {}),
        '^[\t]*([A-Z][a-z]+)+': ('Keyword', (0, 0), {'foreground': '#ff0080'}),
        '^[\t]*(\.){0,1}[a-z_]+:': (
            'Attribute', (0, 1), {'foreground': '#00ffff'}
        ),
        '(\'|")(?!#).+(\'|")': ('String', (0, 0), {'foreground': '#ffff80'}),
        'True|False|None': ('Variables', (0, 0), {'foreground': '#cc00cc'}),
        '[0-9]+(\.[0-9]+){0,1}, ': (
            'Numbers1', (0, 2), {'foreground': '#cc00cc'}
        ),
        ', [0-9]+(\.[0-9]+){0,1}': (
            'Numbers2', (2, 0), {'foreground': '#cc00cc'}
        ),
        ': [0-9]+(\.[0-9]+){0,1}': (
            'Numbers3', (2, 0), {'foreground': '#cc00cc'}
        ),
        '\{|\}|\[|\]|\(|\)': (
            'Brackets', (0, 0), {'foreground': '#ff0080'}
        )
    },
    'py_area': {
        '(import |from |global |if |elif |with |for )': (
            'Keyword', (0, 0), {'foreground': '#ff0080'}
        ),
        '(|while |match | in |pass|^[\t]*try|except| not | is |return )': (
            'Keyword', (0, 0), {'foreground': '#ff0080'}
        ),
        'else:': ('Else', (0, 1), {'foreground': '#ff0080'}),
        "('|\").*('|\")": ('String', (0, 0), {'foreground': '#ffff80'}),
        '^[\t]*[A-Z_]+ =': ('Global1', (0, 2), {'foreground': '#cc00cc'}),
        'global [A-Z_]+': ('Global2', (7, 0), {'foreground': '#cc00cc'}),
        " f'[a-zA-Z\{]": ('Fstring', (0, 1), {'foreground': '#00ffff'}),
        '^def ': ('Cyan', (0, 1), {'foreground': '#00ffff'}),
        '(open|enumerate|zip)\(': (
            'Builtin', (0, 1), {'foreground': '#00ffff'}
        ),
        '^def [a-zA-Z_]+\(': ('Function', (4, 1), {'foreground': '#00ff00'}),
        '\.[a-zA-Z_]+\(': ('Method', (1, 1), {'foreground': '#00ffff'}),
        '\+|\*|\-|/|\(|\)|\{|\}|\[|\]|=|>|<': (
            'Operator', (0, 0), {'foreground': '#ff0080'}
        ),
        'None|True|False': ('Purple', (0, 0), {'foreground': '#cc00cc'}),
        '[0-9]+(\.[0-9]+){0,1}, ': (
            'Numbers1', (0, 2), {'foreground': '#cc00cc'}
        ),
        ', [0-9]+(\.[0-9]+){0,1}': (
            'Numbers2', (2, 0), {'foreground': '#cc00cc'}
        ),
        ': [0-9]+(\.[0-9]+){0,1}': (
            'Numbers3', (2, 0), {'foreground': '#cc00cc'}
        ),
        ' [0-9]+(\.[0-9]+){0,1}$': (
            'Numbers4', (0, 0), {'foreground': '#cc00cc'}
        )
    }
}

SYNTAX['style_area'] = SYNTAX['py_area']
SYNTAX['template_area'] = SYNTAX['tk_area']


def get_background(color: str) -> str:
    """
    Returns a background color based on the given color, is used to highlight
    hex colors in the syntax.
    Params:
        color: hex color. #xxxxxx
    Returns:
        #181818 or #ffffff
    """

    ##### List comprehension to eval each color #####
    r, g, b = [eval(f'0x{color[2*i+1:2*i+3]}') for i in range(3)]

    ##### Multiply by weights based on stackoverflow #####
    r *= 0.299
    g *= 0.587
    b *= 0.114

    ##### Return dark gray if the lightness is high enough, else white #####
    return '#181818' if r + g + b > 40 else '#ffffff'


def highlight(*e):
    """
    Highlight the current TextArea based on its corresponding syntax dict.
    """
    ##### Get the current text from the current frame of the container #####
    textarea = container.current_frame.text

    ##### Get the corresponding syntax dict #####
    syntax = SYNTAX[container.current]

    ##### Remove all previous tags #####
    for tag in textarea.text.tag_names():
        textarea.text.tag_remove(tag, '1.0', 'end')

    ##### Get all the lines from the text #####
    lines = textarea.read().split('\n')

    ##### Check each row and line and for each also check syntax #####
    for row, line in enumerate(lines):
        for regex, (name, boundaries, values) in syntax.items():
            for match in re.finditer(regex, line):
                ##### Start and end of the regex match #####
                start = f'{row+1}.{match.start()+boundaries[0]}'
                end = f'{row+1}.{match.end()-boundaries[1]}'

                ##### If the regex category then add custom properties #####
                if name == 'Color':
                    color = textarea.text.get(start, end)
                    color_config = {
                        'foreground': color,
                        'background': get_background(color)
                    }
                    textarea.tag_add(f'{name} {color}', start, end)
                    textarea.tag_config(
                        f'{name} {color}', **(values | color_config)
                    )
                ##### Else add the tag and config its properties #####
                else:
                    textarea.tag_add(name, start, end)
                    textarea.tag_config(name, **values)


def load_frame(view: str) -> None:
    """
    Shows the given frame based on its Id and highlight its syntax.
    Params:
        view: id of the frame to show.
    """
    container.show_frame(view)
    highlight()


def start_thread() -> None:
    """
    Runs a subprocess to run the simulation of the UI. At the end removes the
    temporary files.
    """
    startupinfo = subprocess.STARTUPINFO()
    startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    subprocess.Popen(['python'] + [f"program_main.pyw"], startupinfo=startupinfo).wait()
    os.remove(f'program_main.pyw')
    os.remove(f'program_main.tk')


def run(e: tk.Event | None) -> None:
    """
    Writes the corresponding files to run the simulation and then create a new
    threading to run it.
    """
    ##### Write the Tk file #####
    with open(f'program_main.tk', 'w') as f:
        f.write(tk_area.text.read().strip())

    ##### Write the Python file #####
    with open(f'program_main.pyw', 'w') as f:
        f.write('from src.tksystem.functions2 import load\n')
        f.write('import sys\n\n')
        f.write('sys.dont_write_bytecode = True\n\n')
        f.write(py_area.text.read().strip())
        f.write('\n\nif __name__ == "__main__":\n')
        f.write(f'\twindow, error = load("program_main.tk", __file__)\n')
        f.write(f'\tif error: print(error)\n')
        f.write('\telse: window.mainloop()')
    highlight()
    ##### Run a new thread #####
    thread = threading.Thread(target=start_thread)
    thread.start()

if __name__ == '__main__':
    ##### Create the main Window and its bindings #####
    window = Window(title='TkSystem 2.0.0')
    window['bg'] = '#262626'
    window.minsize(1000, 700)
    window.geometry(f'1000x700+900+170')
    window.bind('<Control-r>', run)
    window.bind('<Control-o>', open_files)
    window.bind('<Control-n>', new_files)
    window.bind('<Control-s>', save_files)
    window.bind('<Control-Key-1>', lambda e: load_frame('tk_area'))
    window.bind('<Control-Key-2>', lambda e: load_frame('py_area'))
    window.bind('<Control-Key-3>', lambda e: load_frame('style_area'))
    window.bind('<Control-Key-4>', lambda e: load_frame('template_area'))
    for letter in ['<Return>', '<space>']:
        window.bind(letter, highlight)

    ##### Create the window menu based on the MENU dict #####
    menu = WindowMenu(window, MENU)

    ##### Create the Container with the corresponding TextFrame #####
    container = Container(window)
    tk_area = TextFrame(container, 'Tk File')
    container.add_frame(tk_area, 'tk_area')
    py_area = TextFrame(container, 'Python File')
    container.add_frame(py_area, 'py_area')
    style_area = TextFrame(container, 'JSON File')
    container.add_frame(style_area, 'style_area')
    template_area = TextFrame(container, 'Templates')
    container.add_frame(template_area, 'template_area')
    container.show_frame('tk_area')
    new_files()
    highlight()

    container.pack(expand=True, fill='both')

    ##### Run with reloader for easier changes #####
    run_with_reloader(window, '<Control-R>')
    # window.mainloop()
