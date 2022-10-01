import parser
import tkinter as tk

while True:
    try:
        text = input('>>> ')
        result, error = parser.run('<TkSystem>', text)
        if error: print(error.as_string())
        else: print(result)
    except KeyboardInterrupt:
        print('exit...')
        break