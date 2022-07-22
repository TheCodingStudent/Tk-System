"""
Module with graphical interface for the management of python packages, has
tools forEncilla upload the package to GitHub and PyPi, allows you to decide
whether to upload to a GitHub repository automatically detecting if the package
has one, in addition to not uploading to PyPi in case we only want to update
the repository. Version 1.0.6 By Armando Chaparro.
"""

import os
import re
import threading
import tkinter as tk
from tkinter.filedialog import askdirectory
from tkinter import ttk


class Uploader(tk.Tk):
    def __init__(self) -> None:
        """
        Uploader creates the app to manage all the configuration to upload
        the package to Pypi and GitHub, is easier than parse all the terminal
        arguments.
        """
        super().__init__('Uploader By Armando Chaparro')
        self.path_entry = tk.Entry(self, width=50)
        self.version_entry = tk.Entry(self, width=15)
        self.commit_entry = tk.Entry(self, width=30)
        self.git_combobox = ttk.Combobox(self, width=15)
        self.regex = '[0-9]+\.[0-9]+\.[0-9]+'
        if not self.change_path():
            self.quit()
    
    def quit(self):
        self.destroy()
        exit()

    def get_version(self) -> None:
        """
        Opens the setup.cfg file and finds the current version with regular
        expressions, then increment the last digit by 1.
        """
        with open(os.path.join(self.path, 'setup.cfg'), 'r') as f:
            self.text = f.read()
            if match := re.search(self.regex, self.text):
                self.old_version = match.group()
            else:
                return
            match self.old_version.split('.'):
                case(x, y, z):
                    self.version = f'{x}.{y}.{int(z) + 1}'
        self.commit = f'version {self.version}'
        self.commit_entry.delete(0, tk.END)
        self.commit_entry.insert(0, self.commit)
        self.version_entry.delete(0, tk.END)
        self.version_entry.insert(0, self.version)

    def validate_version(self) -> None:
        """
        Checks if the current version is valid, it must follow the pattern:
        x.x.x, if it doesnt then is deleted to prevent any error.
        """
        text = self.version_entry.get()
        if re.match(f'^{self.regex}$', text):
            self.version = text
            self.version_status['fg'] = '#00ff00'
            self.version_status['text'] = 'Valid version'
        else:
            self.version_status['fg'] = '#ff0000'
            self.version_status['text'] = 'Invalid version'
            self.version_entry.delete(0, tk.END)

    def upload(self) -> None:
        """
        Based on the PYPI and GITHUB variables, uploads to their respective
        sites using the same commands that are used in terminal.
        """
        if self.pypi is True:
            if self.delete is True:
                path = os.path.join(self.path, 'dist')
                for file in os.listdir(path):
                    os.remove(os.path.join(path, file))

            with open(os.path.join(self.path, 'setup.cfg'), 'w') as f:
                f.write(self.text.replace(self.old_version, self.version))

            os.system('python -m build')
            file1 = os.path.join(
                self.path, f'dist/tksystem-{self.version}-py3-none-any.whl'
            )
            file2 = os.path.join(
                self.path, f'dist/tksystem-{self.version}.tar.gz'
            )
            os.system(f'twine upload {file1} {file2}')
            print(f'{10*"-"}uploaded to Pypi{10*"-"}')

        if self.github is True:
            os.system('git add .')
            os.system(f'git commit -m "{self.commit}"')
            os.system('git push')
            print(f'{10*"-"}uploaded to GitHub{10*"-"}')

    def get_values(self) -> None:
        """
        Updates all global variables and starts a new thread to run the
        uploading, the thread is necessary to run in parallel with the UI.
        """
        self.commit = self.commit_entry.get()
        self.version = self.version_entry.get()
        self.github = self.git_combobox.current() == 0
        self.pypi = self.pypi_combobox.current() == 0
        self.delete = self.delete_combobox.current() == 0
        thread = threading.Thread(target=self.upload)
        thread.start()

    def change_path(self) -> None:
        """
        Updates the path to upload from.
        """
        self.path = askdirectory()
        if not self.path:
            return False
        
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, self.path)
        git_repo = os.path.exists(os.path.join(self.path, '.git'))
        self.commit_entry['state'] = 'normal' if git_repo else 'disabled'
        self.git_combobox['state'] = 'readonly' if git_repo else 'disabled'
        try:
            self.get_version()
        except FileNotFoundError:
            self.version_entry.delete(0, tk.END)
            self.commit_entry.delete(0, tk.END)
        return True

    def update_git(self, event: tk.Event) -> None:
        """
        Updates all the widgets related to git configuration.
        """
        if self.git_combobox.current():
            self.commit_entry['state'] = 'disabled'
        else:
            self.commit_entry['state'] = 'normal'

    def update_pypi(self, event: tk.Event) -> None:
        """
        Updates all the widgets related to Pypi configuration.
        """
        if self.pypi_combobox.current():
            self.version_entry['state'] = 'disabled'
            self.delete_combobox['state'] = 'disabled'
            self.commit_entry.delete(0, tk.END)
            self.commit_entry.insert(0, '')
        else:
            self.version_entry['state'] = 'normal'
            self.delete_combobox['state'] = 'normal'
            self.commit_entry.delete(0, tk.END)
            self.commit_entry.insert(0, self.commit)

    def run(self) -> None:
        """
        Main function of Uploader, it creates all the UI and bindings.
        """
        path_label = tk.Label(self, text='Folder')
        path_label.grid(row=0, column=0, padx=5, sticky='w')
        self.path_entry.grid(row=0, column=1, padx=5, sticky='w')
        path_button = tk.Button(
            self, text='Change', command=self.change_path
        )
        path_button.grid(row=0, column=2, padx=5, sticky='w')

        version_label = tk.Label(self, text='Version')
        version_label.grid(row=1, column=0, padx=5, sticky='w')
        self.version_entry.grid(row=1, column=1, padx=5, sticky='w')
        version_button = tk.Button(
            self, text='Validate', command=self.validate_version
        )
        version_button.grid(row=1, column=2, padx=5)
        self.version_status = tk.Label(self, text='')
        self.version_status.grid(row=1, column=3, padx=5)

        git_label = tk.Label(self, text='Upload to GIT')
        git_label.grid(row=2, column=0, padx=5, sticky='w')
        self.git_combobox['values'] = ['True', 'False']
        self.git_combobox.bind("<<ComboboxSelected>>", self.update_git)
        self.git_combobox.current(0)
        self.git_combobox.grid(row=2, column=1, padx=5, sticky='w')

        commit_label = tk.Label(self, text='Commit')
        commit_label.grid(row=3, column=0, padx=5, sticky='w')
        self.commit_entry.grid(row=3, column=1, padx=5, sticky='w')

        pypi_label = tk.Label(self, text='Upload to Pypi')
        pypi_label.grid(row=4, column=0, padx=5, sticky='w')
        self.pypi_combobox = ttk.Combobox(self, width=15)
        self.pypi_combobox.bind("<<ComboboxSelected>>", self.update_pypi)
        self.pypi_combobox['values'] = ['True', 'False']
        self.pypi_combobox['state'] = 'readonly'
        self.pypi_combobox.current(0)
        self.pypi_combobox.grid(row=4, column=1, padx=5, sticky='w')

        delete_label = tk.Label(self, text='Delete Previews Dist')
        delete_label.grid(row=5, column=0, padx=5, sticky='w')
        self.delete_combobox = ttk.Combobox(self, width=15)
        self.delete_combobox['values'] = ['True', 'False']
        self.delete_combobox['state'] = 'readonly'
        self.delete_combobox.current(0)
        self.delete_combobox.grid(row=5, column=1, padx=5, sticky='w')

        upload_button = tk.Button(
            self, text='Upload', command=self.get_values
        )
        upload_button.grid(row=6, column=1, padx=5, pady=10, sticky='ew')

        self.mainloop()


if __name__ == '__main__':
    app = Uploader()
    app.run()
