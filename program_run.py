from tksystem.functions import load
import sys

sys.dont_write_bytecode = True

STYLE = {

}

if __name__ == '__main__':
	window = load('program_run.tk', __file__, style_dict=STYLE)
	window.mainloop()