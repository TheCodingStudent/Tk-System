from pylejandria.tools import get_module, pair


def clean_text(text):
    clean_lines = []
    for line in text.split('\n'):
        if not line: continue
        if all([char in ('\t', ' ') for char in line]): continue
        clean_lines.append(line)
    return clean_lines


def parse_file(text):
    properties, start_index = [], 0
    key_points = [line for line in text if ':' not in line] + [None]
    for point_a, point_b in pair(key_points, 2):
        properties.append({})
        index_a = text.index(point_a, start_index)
        index_b = text.index(point_b, start_index) if point_b else len(text)
        properties[-1]['widget'] = text[index_a].strip()
        properties[-1]['indent'] = text[index_a].count('\t')
        start_index = index_b

        
    


def load(tk_filename, file):
    module = get_module(file)
    module_dict = {key:getattr(module, key) for key in dir(module)}
    with open(tk_filename, 'r') as f: tk_text = f.read()
    tk_text = clean_text(tk_text)
    parsed_file = parse_file(tk_text)

    return None, True