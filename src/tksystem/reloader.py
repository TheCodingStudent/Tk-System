import os, sys, subprocess


class Reloader(object):
    RELOADING_CODE = 3
    def start_process(self):
        """Spawn a new Python interpreter with the same arguments as this one,
        but running the reloader thread.
        """
        while True:
            args = [sys.executable] + sys.argv
            env = os.environ.copy()
            env['TKINTER_MAIN'] = 'true'
            exit_code = subprocess.call(args, env=env, close_fds=False)
            if exit_code != self.RELOADING_CODE:
                return exit_code

    def trigger_reload(self):
        sys.exit(self.RELOADING_CODE)


def run_with_reloader(root, *hotkeys):
    """Run the given application in an independent python interpreter."""
    import signal
    signal.signal(signal.SIGTERM, lambda *args: sys.exit(0))
    reloader = Reloader()
    try:
        if os.environ.get('TKINTER_MAIN') == 'true':
            for hotkey in hotkeys:
                root.bind_all(hotkey, lambda event: reloader.trigger_reload())
            root.mainloop()
        else:
            sys.exit(reloader.start_process())
    except KeyboardInterrupt:
        pass


if __name__ == "__main__":
    from tkinter import Tk, Label
    
    class App(Tk):
        def __init__(self):
            Tk.__init__(self)

            Label(self, text="Press Control+r to reload...").pack()
            Label(self, text="Updated...").pack()

    run_with_reloader(App(), "<Control-R>", "<Control-r>")