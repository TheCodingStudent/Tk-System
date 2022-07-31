from string import ascii_letters as LETTERS
from tkinter import TclError, Tk

##### VARIABLES #####
DIGITS = '0123456789'
OPERATORS = {
    '+': 'PLUS',
    '*': 'MUL',
    '/': 'DIV',
    '(': 'LPAREN',
    ')': 'RPAREN',
    '[': 'LSQUARE',
    ']': 'RSQUARE',
    '{': 'LCURLY',
    '}': 'RCURLY',
    '^': 'POWER',
    ',': 'COMMA',
    ':': 'COLON'
}

COMPOSITE = {
    '<': 'LT',
    '>': 'GT',
    '=': 'EQ',
    '!': 'NA',
    '-': 'MINUS',
    '->': 'ARROW',
    '<=': 'LTE',
    '>=': 'GTE',
    '!=': 'NE',
    '==': 'EE'
}

ESCAPE_CHARACTERS = {
    'n': '\n',
    't': '\t'
}

LETTERS_DIGITS = LETTERS + DIGITS
KEYWORDS = ['and', 'or', 'not', 'lambda']

def string_with_arrows(text, pos_start, pos_end):
    result = ''
    idx_start = max(text.rfind('\n', 0, pos_start.index), 0)
    idx_end = text.find('\n', idx_start + 1)
    if idx_end < 0: idx_end = len(text)
    line_count = pos_end.line - pos_start.line + 1
    for i in range(line_count):
        line = text[idx_start:idx_end]
        col_start = pos_start.column if i == 0 else 0
        col_end = pos_end.column if i == line_count - 1 else len(line) - 1
        result += line + '\n'
        result += ' ' * col_start + '^' * (col_end - col_start)
        idx_start = idx_end
        idx_end = text.find('\n', idx_start + 1)
        if idx_end < 0: idx_end = len(text)

    return result.replace('\t', '')

#######################################
# ERRORS
#######################################

class Error:
    def __init__(self, start, end, error_name, details):
        self.start = start
        self.end = end
        self.error_name = error_name
        self.details = details
    
    def as_string(self, row=None):
        result = f'{self.error_name}: {self.details}'
        result += f'. File {self.start.filename}, line {self.start.line + 1 if not row else row}'
        result += f'\n\n{string_with_arrows(self.start.filetext, self.start, self.end)}'
        return result


class IllegalCharError(Error):
    def __init__(self, start, end, details):
        super().__init__(start, end, 'Illegal Character', details)


class InvalidSyntaxError(Error):
    def __init__(self, start, end, details=''):
        super().__init__(start, end, 'Invalid Syntax', details)


class MethodError(Error):
    def __init__(self, start, end, details=''):
        super().__init__(start, end, 'Invalid Method', details)


class RTError(Error):
    def __init__(self, start, end, details, context):
        super().__init__(start, end, 'RunTimeError', details)
        self.context = context
    
    def as_string(self, row=None):
        result = self.generate_traceback(row)
        result += f'{self.error_name}: {self.details}'
        result += f'\n\n{string_with_arrows(self.start.filetext, self.start, self.end)}'
        return result
    
    def generate_traceback(self, row=None):
        result = ''
        pos = self.start
        context = self.context
        while context:
            result = f'  File {pos.filename}, line {pos.line + 1 if not row else row} in {context.name}\n' + result
            pos = context.parent_pos
            context = context.parent
        
        return f'Traceback (most recent call last): \n{result}'

#######################################
# TOKEN
#######################################

class Token:
    def __init__(self, type_, value=None, start=None, end=None):
        self.type = type_
        self.value = value

        if start:
            self.start = start.copy()
            self.end = self.start.copy()
            self.end.advance()
        
        if end:
            self.end = end.copy()
    
    def matches(self, type_, value):
        return self.type == type_ and self.value == value
    
    def __repr__(self):
        if self.value: return f'{self.type}:{self.value}'
        return f'{self.type}'

#######################################
# POSITION
#######################################

class Position:
    def __init__(self, index, line, column, filename, filetext):
        self.index = index
        self.line = line
        self.column = column
        self.filename = filename
        self.filetext = filetext
    
    def advance(self, current_char=None):
        self.index += 1
        self.column += 1
        if current_char == '\n':
            self.line += 1
            self.column = 0
        return self
    
    def recede(self):
        self.index -= 1
        self.column -= 1
        return self
    
    def copy(self):
        return Position(self.index, self.line, self.column, self.filename, self.filetext)

#######################################
# LEXER
#######################################

class Lexer:
    def __init__(self, filename, text):
        self.filename = filename
        self.text = text
        self.pos = Position(-1, 0, -1, filename, text)
        self.current_char = None
        self.advance()
    
    def advance(self):
        self.pos.advance(self.current_char)
        self.current_char = self.text[self.pos.index] if self.pos.index < len(self.text) else None
    
    def make_number(self):
        num_str = ''
        dot_count = 0
        start = self.pos.copy()

        while self.current_char != None and self.current_char in DIGITS + '.':
            if self.current_char == '.':
                if dot_count == 1: break
                dot_count += 1
                num_str += '.'
            else:
                num_str += self.current_char
            self.advance()
        
        if dot_count == 0:
            return Token('INT', int(num_str), start=start, end=self.pos)
        return Token('FLOAT', float(num_str), start=start, end=self.pos)
    
    def make_identifier(self):
        id_str = ''
        start = self.pos.copy()
        
        while self.current_char != None and self.current_char in LETTERS_DIGITS + '_':
            id_str += self.current_char
            self.advance()
        
        token_type = 'KEYWORD' if id_str in KEYWORDS else 'IDENTIFIER'
        return Token(token_type, id_str, start, self.pos)

    def make_operator(self):
        start = self.pos.copy()
        op_str = self.current_char
        self.advance()

        while self.current_char != None and op_str + self.current_char in COMPOSITE.keys():
            op_str += self.current_char
            self.advance()
        
        if op_str in ('!', ):
            return None, InvalidSyntaxError(start, self.pos, "Expected '!=' or '=='")

        return Token(COMPOSITE.get(op_str), start=start, end=self.pos), None
    
    def make_string(self, quote):
        string = ''
        start = self.pos.copy()
        escape = False
        self.advance()

        while self.current_char != quote and self.current_char != None:
            if escape:
                string += ESCAPE_CHARACTERS.get(self.current_char, self.current_char)
            elif self.current_char == '\\':
                escape = True
            else:
                string += self.current_char
            self.advance()
            escape = False
        
        if self.current_char != quote:
            return None, InvalidSyntaxError(start, self.pos, f"Expected {quote}")
        
        self.advance()
        return Token('STRING', string, start, self.pos), None

    def skip_comment(self):
        self.advance()
        while self.current_char:
            self.advance()
        self.advance()

    def make_tokens(self):
        tokens = []

        while self.current_char is not None:
            if self.current_char in ' \t':
                self.advance()
            elif self.current_char in OPERATORS.keys():
                tokens.append(Token(OPERATORS[self.current_char], start=self.pos))
                self.advance()
            elif self.current_char in DIGITS:
                tokens.append(self.make_number())
            elif self.current_char in LETTERS_DIGITS + '_':
                tokens.append(self.make_identifier())
            elif self.current_char in COMPOSITE.keys():
                token, error = self.make_operator()
                if error: return [], error
                tokens.append(token)
            elif self.current_char == '"':
                token, error = self.make_string('"')
                if error: return [], error
                tokens.append(token)
            elif self.current_char == "'":
                token, error = self.make_string("'")
                if error: return [], error
                tokens.append(token)
            elif self.current_char == '#':
                self.skip_comment()
            elif self.current_char == '.':
                tokens.append(Token('DOT', start=self.pos))
                self.advance()
            else:
                start = self.pos.copy()
                char = self.current_char
                self.advance()
                return [], IllegalCharError(start, self.pos, f"'{char}'")

        tokens.append(Token('EOF', start=self.pos))
        return tokens, None

#######################################
# NODES
#######################################

class NumberNode:
    def __init__(self, token):
        self.token = token
        self.start = self.token.start
        self.end = self.token.end
    
    def __repr__(self):
        return f'{self.token}'


class StringNode:
    def __init__(self, token):
        self.token = token
        self.start = self.token.start
        self.end = self.token.end
    
    def __repr__(self):
        return f'{self.token}'


class BinOpNode:
    def __init__(self, left_node, op_token, right_node):
        self.left_node = left_node
        self.op_token = op_token
        self.right_node = right_node
        self.start = self.left_node.start
        self.end = self.right_node.end
    
    def __repr__(self):
        return f'({self.left_node}, {self.op_token}, {self.right_node})'


class UnaryOpNode:
    def __init__(self, op_token, node):
        self.op_token = op_token
        self.node = node
        self.start = self.op_token.start
        self.end = self.node.end
    
    def __repr__(self):
        return f'({self.op_token}, {self.node})'


class VarAccessNode:
    def __init__(self, var_name):
        self.name = var_name
        self.start = self.name.start
        self.end = self.name.end


class MethodAccessNode:
    def __init__(self, var_name, methods, attribute=None):
        self.name = var_name
        self.methods = methods
        self.attribute = attribute
        self.start = self.name.start
        if self.attribute:
            self.end = self.attribute.end
        elif self.methods:
            self.end = self.methods[-1].end
        else:
            self.end = self.name.end


class FuncDefNode:
    def __init__(self, var_name, args_name, body_node):
        self.name = var_name
        self.args = args_name
        self.body = body_node

        if self.name:
            self.start = self.name.start
        elif len(self.args) > 0:
            self.start = self.args[0].start
        else:
            self.start = self.body.start
        
        self.end = self.body.end


class CallNode:
    def __init__(self, node, arg_nodes):
        self.node = node
        self.args = arg_nodes

        self.start = self.node.start
        if len(self.args) > 0:
            self.end = self.args[-1].end
        else:
            self.end = self.node.end


class ListNode:
    def __init__(self, elements, start, end):
        self.elements = elements
        self.start = start
        self.end = end


class DictNode:
    def __init__(self, keys, values, start, end):
        self.keys = keys
        self.values = values
        self.start = start
        self.end = end

#######################################
# PARSER
#######################################

class ParseResult:
    def __init__(self):
        self.error = None
        self.node = None
        self.advance_count = 0
    
    def register_advance(self):
        self.advance_count += 1
    
    def register_reverse(self):
        self.advance_count -= 1
    
    def register(self, res):
        self.advance_count += res.advance_count
        if res.error: self.error = res.error
        return res.node

    def success(self, node):
        self.node = node
        return self

    def failure(self, error):
        if not self.error or self.advance_count == 0:
            self.error = error
        return self
    
    def __repr__(self):
        if self.error:
            return self.error.as_string()
        return 'No error'


class Parser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.index = -1
        self.advance()
    
    def advance(self):
        self.index += 1
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
        return self.current_token
    
    def reverse(self):
        self.index -= 1
        if self.index < len(self.tokens):
            self.current_token = self.tokens[self.index]
        return self.current_token
    
    def parse(self):
        res = self.expr()
        if not res.error and self.current_token.type != 'EOF':
            return res.failure(InvalidSyntaxError(
                self.current_token.start, self.current_token.end,
                "Expected '+', '-', '/' or '*'"
            ))
        return res
    
    def atom(self):
        res = ParseResult()
        token = self.current_token

        if token.type in ('INT', 'FLOAT'):
            res.register_advance()
            self.advance()
            return res.success(NumberNode(token))
        
        elif token.type == 'STRING':
            res.register_advance()
            self.advance()
            return res.success(StringNode(token))

        elif token.type == 'IDENTIFIER':
            res.register_advance()
            self.advance()
            return res.success(VarAccessNode(token))

        elif token.type == 'LPAREN':
            res.register_advance()
            self.advance()
            expr = res.register(self.expr())
            if res.error: return res
            if self.current_token.type == 'RPAREN':
                res.register_advance()
                self.advance()
                return res.success(expr)
            return res.failure(InvalidSyntaxError(
                self.current_token.start, self.current_token.end,
                "Expected ')'"
            ))
        
        elif token.matches('KEYWORD', 'lambda'):
            func_def = res.register(self.func_def())
            if res.error: return res
            return res.success(func_def)

        elif token.type == 'LSQUARE':
            list_expr = res.register(self.list_expr())
            if res.error: return res
            return res.success(list_expr)

        elif token.type == 'LCURLY':
            dict_expr = res.register(self.dict_expr())
            if res.error: return res
            return res.success(dict_expr)

        return res.failure(InvalidSyntaxError(
            token.start, token.end,
            "Expected int, float, identifier, '+', '-', '(', '[' or '{'"
        ))
    
    def power(self):
        res = ParseResult()
        node = res.register(self.bin_op(self.call, ('POWER', ), self.factor))
        if res.error: return res
        if isinstance(node, CallNode):
            return res.success(node)
        
        if self.current_token.type not in ('DOT', 'LSQUARE'):
            return res.success(node)
        
        methods = []
        property_ = None
        while self.current_token.type == 'DOT':
            res.register_advance()
            self.advance()
            if self.current_token.type != 'IDENTIFIER':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    'Expected method name'
                ))
            methods.append(self.current_token)
            res.register_advance()
            self.advance()
        
        if self.current_token.type == 'LSQUARE':
            res.register_advance()
            self.advance()
            if self.current_token.type != 'STRING':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    'Expected attribute'
                ))
            property_ = self.current_token
            res.register_advance()
            self.advance()
            if self.current_token.type != 'RSQUARE':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected ']'"
                ))
            res.register_advance()
            self.advance()
        
        return res.success(MethodAccessNode(node.name, methods, property_))
    
    def call(self):
        res = ParseResult()
        atom = res.register(self.atom())
        if res.error: return res

        if self.current_token.type == 'LPAREN':
            res.register_advance()
            self.advance()
            args = []

            if self.current_token.type == 'RPAREN':
                res.register_advance()
                self.advance()
            else:
                args.append(res.register(self.expr()))
                if res.error: 
                    return res.failure(InvalidSyntaxError(
                        self.current_token.start, self.current_token.end,
                        "Expected ')', 'lambda', int, float, identifier, '+', '-', '(', '[' or 'not'"
                    ))
                
                while self.current_token.type == 'COMMA':
                    res.register_advance()
                    self.advance()
                    args.append(res.register(self.expr()))
                    if res.error: return res

                if self.current_token.type != 'RPAREN':
                    return res.failure(InvalidSyntaxError(
                        self.current_token.start, self.current_token.end,
                        "Expected ',' or ')'"
                    ))

                res.register_advance()
                self.advance()

            return res.success(CallNode(atom, args))

        return res.success(atom)
                
    def factor(self):
        res = ParseResult()
        token = self.current_token

        if token.type in ('PLUS', 'MINUS'):
            res.register_advance()
            self.advance()
            factor = res.register(self.factor())
            if res.error: return res
            return res.success(UnaryOpNode(token, factor))

        return self.power()
    
    def bin_op(self, func_a, ops, func_b=None):
        if func_b is None:
            func_b = func_a

        res = ParseResult()
        left = res.register(func_a())
        if res.error: return res
        while self.current_token.type in ops or (self.current_token.type, self.current_token.value) in ops:
            op_token = self.current_token
            res.register_advance()
            self.advance()
            right = res.register(func_b())
            if res.error: return res
            left = BinOpNode(left, op_token, right)
        
        return res.success(left)

    def term(self):
        return self.bin_op(self.factor, ('MUL', 'DIV'))
    
    def arith_expr(self):
        return self.bin_op(self.term, ('PLUS', 'MINUS'))
    
    def comp_expr(self):
        res = ParseResult()
        if self.current_token.matches('KEYWORD', 'not'):
            op_token = self.current_token
            res.register_advance()
            self.advance()

            node = res.register(self.comp_expr())
            if res.error: return res
            return res.success(UnaryOpNode(op_token, node))
        
        node = res.register(self.bin_op(self.arith_expr, ('EE', 'NE', 'LT', 'GT', 'LTE', 'GTE')))
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.start, self.current_token.end,
                "Expected int, float, identifier, '+', '-', '(', '[' or 'not'"
            ))
        return res.success(node)
    
    def expr(self):
        res = ParseResult()
        node = res.register(self.bin_op(self.comp_expr, (('KEYWORD', 'and'), ('KEYWORD', 'or'))))
        if res.error:
            return res.failure(InvalidSyntaxError(
                self.current_token.start, self.current_token.end,
                "Expected 'lambda', int, float, identifier, '+', '-', '(', '[' or 'not'"
            ))
        return res.success(node)

    def func_def(self):
        res = ParseResult()
        res.register_advance()
        self.advance()

        if self.current_token.type == 'IDENTIFIER':
            var_name = self.current_token
            res.register_advance()
            self.advance()
            if self.current_token.type != 'LPAREN':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    f"Expected '('"
                ))
        else:
            var_name = None
            if self.current_token.type != 'LPAREN':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    f"Expected identifier or '('"
                ))
        
        res.register_advance()
        self.advance()
        args = []

        if self.current_token.type == 'IDENTIFIER':
            args.append(self.current_token)
            res.register_advance()
            self.advance()

            while self.current_token.type == 'COMMA':
                res.register_advance()
                self.advance()
                if self.current_token.type != 'IDENTIFIER':
                    return res.failure(InvalidSyntaxError(
                        self.current_token.start, self.current_token.end,
                        'Expected identifier'
                    ))
                args.append(self.current_token)
                res.register_advance()
                self.advance()
        
            if self.current_token.type != 'RPAREN':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    f"Expected ',' or ')'"
                ))
        elif self.current_token.type != 'RPAREN':
            return res.failure(InvalidSyntaxError(
                self.current_token.start, self.current_token.end,
                f"Expected ',' or ')'"
            ))
        
        res.register_advance()
        self.advance()

        if self.current_token.type != 'ARROW':
            return res.failure(InvalidSyntaxError(
                self.current_token.start, self.current_token.end,
                "Expected ->"
            ))
        
        res.register_advance()
        self.advance()

        node = res.register(self.expr())
        if res.error: return res

        return res.success(FuncDefNode(
            var_name,
            args,
            node
        ))

    def list_expr(self):
        res = ParseResult()
        elements = []
        start = self.current_token.start.copy()

        res.register_advance()
        self.advance()

        if self.current_token.type == 'RSQUARE':
            res.register_advance()
            self.advance()
        else:
            elements.append(res.register(self.expr()))
            if res.error: 
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected ']', 'lambda', int, float, identifier, '+', '-', '(', '[' or 'not'"
                ))
            
            while self.current_token.type == 'COMMA':
                res.register_advance()
                self.advance()
                elements.append(res.register(self.expr()))
                if res.error: return res

            if self.current_token.type != 'RSQUARE':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected ',' or ']'"
                ))

            res.register_advance()
            self.advance()
        
        return res.success(ListNode(
            elements,
            start,
            self.current_token.end.copy()
        ))
    
    def dict_expr(self):
        res = ParseResult()
        keys = []
        values = []
        start = self.current_token.start.copy()

        res.register_advance()
        self.advance()

        if self.current_token.type == 'RCURLY':
            res.register_advance()
            self.advance()
        else:
            if self.current_token.type != 'STRING':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected '}' or string"
                ))
            
            keys.append(res.register(self.atom()))
            if res.error: return res

            if self.current_token.type != 'COLON':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected ':'"
                ))
            res.register_advance()
            self.advance()
            values.append(res.register(self.expr()))
            if res.error: 
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected 'lambda', int, float, string, identifier, '+', '-', '(', '[', '{' or 'not'"
                ))
        
            while self.current_token.type == 'COMMA':
                res.register_advance()
                self.advance()
                if self.current_token.type != 'STRING':
                    return res.failure(InvalidSyntaxError(
                        self.current_token.start, self.current_token.end,
                        "Expected string"
                    ))
                keys.append(res.register(self.atom()))
                if res.error: return res
                if self.current_token.type != 'COLON':
                    return res.failure(InvalidSyntaxError(
                        self.current_token.start, self.current_token.end,
                        "Expected ':'"
                    ))
                res.register_advance()
                self.advance()
                values.append(res.register(self.expr()))
                if res.error: 
                    return res.failure(InvalidSyntaxError(
                        self.current_token.start, self.current_token.end,
                        "Expected 'lambda', int, float, string, identifier, '+', '-', '(', '[', '{' or 'not'"
                    ))
            
            if self.current_token.type != 'RCURLY':
                return res.failure(InvalidSyntaxError(
                    self.current_token.start, self.current_token.end,
                    "Expected ',' or '}'"
                ))

            res.register_advance()
            self.advance()
    
        return res.success(DictNode(
            keys,
            values,
            start,
            self.current_token.end.copy()
        ))


#######################################
# RUNTIME RESULT
#######################################

class RTResult:
    def __init__(self):
        self.value = None
        self.error = None
    
    def register(self, res):
        if res.error: self.error = res.error
        return res.value
    
    def success(self, value):
        self.value = value
        return self
    
    def failure(self, error):
        self.error = error
        return self

#######################################
# VALUES
#######################################

class Value:
    def __init__(self):
        self.set_pos()
        self.set_context()
    
    def set_pos(self, start=None, end=None):
        self.start = start
        self.end = end
        return self
    
    def set_context(self, context=None):
        self.context = context
        return self
    
    def plus(self, other):
        return None, self.illegal_operation(other)
    
    def minus(self, other):
        return None, self.illegal_operation(other)
    
    def mul(self, other):
        return None, self.illegal_operation(other)

    def power(self, other):
        return None, self.illegal_operation(other)
    
    def div(self, other):
        return None, self.illegal_operation(other)
    
    def ee(self, other):
        return None, self.illegal_operation(other)
    
    def ne(self, other):
        return None, self.illegal_operation(other)
        
    def lt(self, other):
        return None, self.illegal_operation(other)
    
    def gt(self, other):
        return None, self.illegal_operation(other)
    
    def lte(self, other):
        return None, self.illegal_operation(other)
    
    def gte(self, other):
        return None, self.illegal_operation(other)

    def notted(self):
        return None, self.illegal_operation()
    
    def anded(self):
        return None, self.illegal_operation()
    
    def ored(self):
        return None, self.illegal_operation()

    def illegal_operation(self, other=None):
        if not other: other = self
        return RTError(
            self.start, other.end,
            'Illegal operation',
            self.context
        )

    def to_python(self):
        return None

    def get_method(self, attribute):
        return None


class Number(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value

    def plus(self, other):
        if isinstance(other, Number):
            return Number(self.value + other.value).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def minus(self, other):
        if isinstance(other, Number):
            return Number(self.value - other.value).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def mul(self, other):
        if isinstance(other, Number):
            return Number(self.value * other.value).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def power(self, other):
        if isinstance(other, Number):
            return Number(self.value ** other.value).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def div(self, other):
        if isinstance(other, Number):
            if other.value == 0:
                return None, RTError(
                    other.start, other.end,
                    'Division by Zero',
                    self.context
                )
            return Number(self.value / other.value).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def ee(self, other):
        if isinstance(other, Number):
            return Number(int(self.value == other.value)).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def ne(self, other):
        if isinstance(other, Number):
            return Number(int(self.value != other.value)).set_context(self.context), None
        return None, self.illegal_operation(other.end)
        
    def lt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value < other.value)).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def gt(self, other):
        if isinstance(other, Number):
            return Number(int(self.value > other.value)).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def lte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value <= other.value)).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def gte(self, other):
        if isinstance(other, Number):
            return Number(int(self.value >= other.value)).set_context(self.context), None
        return None, self.illegal_operation(other.end)
    
    def notted(self):
        return Number(0 if self.value != 0 else 1).set_context(self.context), None

    def ored(self, other):
        if isinstance(other, Number):
            return Number(int(self.value or other.value)).set_context(self.context), None
        return None, self.illegal_operation(other)
    
    def anded(self, other):
        if isinstance(other, Number):
            return Number(int(self.value and other.value)).set_context(self.context), None
        return None, self.illegal_operation(other)

    def copy(self):
        copy = Number(self.value)
        copy.set_pos(self.start, self.end)
        copy.set_context(self.context)
        return copy
    
    def __repr__(self):
        return str(self.value)

    def to_python(self):
        return self.value


class BaseFunction(Value):
    def __init__(self, name):
        super().__init__()
        self.name = name or '<lambda>'
    
    def generate_new_context(self):
        new_context = Context(self.name, self.context, self.start)
        new_context.symbol_table = SymbolTable(new_context.parent.symbol_table)
        return new_context
    
    def check_args(self, arg_names, args):
        res = RTResult()
        if len(args) > len(arg_names):
            return res.failure(RTError(
                self.start, self.end,
                f"too many args passed into '{self.name}. Expected {len(arg_names)}'",
                self.context
            ))
        
        if len(args) < len(arg_names):
            return res.failure(RTError(
                self.start, self.end,
                f"too few args passed into '{self.name}. Expected {len(arg_names)}'",
                self.context
            ))

        return res.success(None)

    def populate_args(self, arg_names, args, context):
        for arg_name, arg_value in zip(arg_names, args):
            arg_value.set_context(context)
            context.symbol_table.set(arg_name, arg_value)
        
    def check_and_populate(self, arg_names, args, context):
        res = RTResult()
        res.register(self.check_args(arg_names, args))
        if res.error: return res
        self.populate_args(arg_names, args, context)
        return res.success(None)


class Function(BaseFunction):
    def __init__(self, name, body, args):
        super().__init__(name)
        self.body = body
        self.args = args
    
    def execute(self, args):
        res = RTResult()
        interpreter = Interpreter()
        new_context = self.generate_new_context()

        res.register(self.check_and_populate(self.args, args, new_context))
        if res.error: return res
        
        value = res.register(interpreter.visit(self.body, new_context))
        if res.error: return res
        return res.success(value)
    
    def copy(self):
        copy = Function(self.name, self.body, self.args)
        copy.set_context(self.context)
        copy.set_pos(self.start, self.end)
        return copy
    
    def __repr__(self):
        return f"<Function '{self.name}'>"


class BuiltInFunction(BaseFunction):
    def __init__(self, name):
        super().__init__(name)
    
    def execute(self, args):
        res = RTResult()
        context = self.generate_new_context()
        method_name = f'execute_{self.name}'
        method = getattr(self, method_name, self.no_visit_method)
        res.register(self.check_and_populate(method.arg_names, args, context))
        if res.error: return res
        return_value = res.register(method(context))
        if res.error: return res
        return res.success(return_value)
    
    def no_visit_method(self, context):
        raise Exception(f'No execute_{self.name} method defined')
    
    def copy(self):
        copy = BuiltInFunction(self.name)
        copy.set_context(self.context)
        copy.set_pos(self.start, self.end)
        return copy
    
    def __repr__(self):
        return f'<built-in function {self.name}>'
    
    def execute_rgb(self, context):
        r = context.symbol_table.get('r').value
        g = context.symbol_table.get('g').value
        b = context.symbol_table.get('b').value

        if not all([isinstance(c, int) for c in [r, g, b]]):
            return RTResult().failure(RTError(
                self.start, self.end,
                "Arguments must be integers",
                context
            ))
        return RTResult().success(
            String(f'#{r:02X}{g:02X}{b:02X}')
        )

    execute_rgb.arg_names = ['r', 'g', 'b']


class String(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def plus(self, other):
        if isinstance(other, String):
            return String(self.value + other.value).set_context(self.context), None
        return None, self.illegal_operation(other)
    
    def mul(self, other):
        if isinstance(other, Number):
            return String(self.value * other.value).set_context(self.context), None
        return None, self.illegal_operation(other)

    def copy(self):
        copy = String(self.value)
        copy.set_context(self.context)
        copy.set_pos(self.start, self.end)
        return copy
    
    def __repr__(self):
        return f'"{self.value}"'

    def to_python(self):
        return self.value


class List(Value):
    def __init__(self, elements):
        super().__init__()
        self.elements = elements
    
    def plus(self, other):
        if isinstance(other, List):
            new_list = self.copy()
            new_list.elements.extend(other.elements)
            return new_list, None
        return None, self.illegal_operation(other)

    def mul(self, other):
        if isinstance(other, Number):
            new_list = self.copy()
            new_list.elements *= other.value
            return new_list, None
        return None, self.illegal_operation(other)

    def copy(self):
        copy = List(self.elements)
        copy.set_pos(self.start, self.end)
        copy.set_context(self.context)
        return copy

    def __repr__(self):
        return f'{self.elements}'

    def to_python(self):
        return [element.to_python() for element in self.elements]


class Dict(Value):
    def __init__(self, keys, values):
        super().__init__()
        self.keys = keys
        self.values = values
    
    def copy(self):
        copy = Dict(self.keys, self.values)
        copy.set_pos(self.start, self.end)
        copy.set_context(self.context)
        return copy
    
    def __repr__(self):
        return '{' + ', '.join([f'{key}:{value}' for key, value in zip(self.keys, self.values)]) + '}'

    def to_python(self):
        return {key.to_python():value.to_python() for key, value in zip(self.keys, self.values)}


class Variable(Value):
    def __init__(self, value):
        super().__init__()
        self.value = value
    
    def get_method(self, method):
        try:
            return Variable(getattr(self.value, method))
        except AttributeError:
            return None

    def get_attribute(self, attribute):
        if self.value is None: return None
        try:
            Variable(self.value[attribute])
        except TclError:
            return None

    def copy(self):
        copy = Variable(self.value)
        copy.set_pos(self.start, self.end)
        copy.set_context(self.context)
        return copy
    
    def __repr__(self):
        return str(self.value)

    def to_python(self):
        return self.value

#######################################
# CONTEXT
#######################################

class Context:
    def __init__(self, name, parent=None, parent_pos=None):
        self.name = name
        self.parent = parent
        self.parent_pos = parent_pos
        self.symbol_table = SymbolTable()

#######################################
# SYMBOL TABLE
#######################################

class SymbolTable:
    def __init__(self, parent=None):
        self.symbols = {}
        self.parent = parent
    
    def get(self, name):
        value = self.symbols.get(name, None)
        if value is None and self.parent:
            return self.parent.symbols.get(name, None)
        return value
    
    def set(self, name, value):
        self.symbols[name] = value
    
    def remove(self, name):
        del self.symbols[name]

#######################################
# INTERPRETER
#######################################

class Interpreter:
    def visit(self, node, context):
        method_name = f'visit_{type(node).__name__}'
        method = getattr(self, method_name, self.no_visit_method)
        return method(node, context)
    
    def no_visit_method(self, node, context):
        raise Exception(f'No  visit_{type(node).__name__} method defined')
    
    def visit_VarAccessNode(self, node, context):
        res = RTResult()
        var_name = node.name.value
        value = context.symbol_table.get(var_name)

        if not value:
            return res.failure(RTError(
                node.start, node.end,
                f"'{var_name}' is not defined",
                context
            ))
        
        value = value.copy().set_pos(node.start, node.end).set_context(context)
        return res.success(value)
    
    def visit_NumberNode(self, node, context):
        return RTResult().success(
            Number(node.token.value).set_context(context).set_pos(node.start, node.end)
        )
    
    def visit_StringNode(self, node, context):
        return RTResult().success(
            String(node.token.value).set_context(context).set_pos(node.start, node.end)
        )

    def visit_BinOpNode(self, node, context):
        res = RTResult()
        left = res.register(self.visit(node.left_node, context))
        if res.error: return res
        right = res.register(self.visit(node.right_node, context))
        if res.error: return res

        if node.op_token.matches('KEYWORD', 'and') or node.op_token.matches('KEYWORD', 'or'):
            func = getattr(left, f'{node.op_token.value.lower()}ed')
        else:
            func = getattr(left, node.op_token.type.lower())
            
        result, error = func(right)
        if error: return res.failure(error)

        return res.success(result.set_context(context).set_pos(node.start, node.end))
    
    def visit_UnaryOpNode(self, node, context):
        res = RTResult()
        number = res.register(self.visit(node.node, context))
        if res.error: return res
        if node.op_token.type == 'MINUS':
            number, error = number.mul(Number(-1))
        elif node.op_token.matches('KEYWORD', 'not'):
            number, error = number.notted()
        if error:
            return res.failure(error)
        return res.success(
            number.set_context(context).set_pos(node.start, node.end)
        )
    
    def visit_FuncDefNode(self, node, context):
        res = RTResult()
        func_name = node.name.value if node.name else None
        body = node.body
        arg_names = [arg_name.value for arg_name in node.args]
        func_value = Function(func_name, body, arg_names).set_context(context).set_pos(node.start, node.end)
        
        if node.name:
            context.symbol_table.set(func_name, func_value)
        
        return res.success(func_value)
    
    def visit_CallNode(self, node, context):
        res = RTResult()
        args = []
        value = res.register(self.visit(node.node, context))
        if res.error: return res
        value = value.copy().set_context(context).set_pos(node.start, node.end)

        for arg_node in node.args:
            args.append(res.register(self.visit(arg_node, context)))
            if res.error: return res
        
        return_value = res.register(value.execute(args))
        if res.error: return res
        return_value = return_value.copy().set_pos(node.start, node.end).set_context(context)
        return res.success(return_value)

    def visit_ListNode(self, node, context):
        res = RTResult()
        elements = []
        for element in node.elements:
            elements.append(res.register(self.visit(element, context)))
            if res.error: return res
        
        return res.success(
            List(elements).set_context(context).set_pos(node.start, node.end)
        )
    
    def visit_DictNode(self, node, context):
        res = RTResult()
        keys = []
        values = []
        for key, value in zip(node.keys, node.values):
            keys.append(res.register(self.visit(key, context)))
            if res.error: return res
            values.append(res.register(self.visit(value, context)))
            if res.error: return res
        
        return res.success(
            Dict(keys, values).set_context(context).set_pos(node.start, node.end)
        )

    def visit_MethodAccessNode(self, node, context):
        res = RTResult()

        var_name = node.name.value
        result = context.symbol_table.get(var_name)

        if not result:
            return res.failure(RTError(
                node.start, node.end,
                f"'{var_name}' is not defined",
                context
            ))
        
        methods = node.methods
        for method in methods:
            if value := result.get_method(method.value):
                result = value
                var_name += f'.{method.value}'
            else:
                return res.failure(RTError(
                    method.start, method.end,
                    f"'{var_name}' has no method '{method.value}'",
                    context
                ))

        if node.attribute:
            try:
                result = Variable(result.value[node.attribute.value])
            except TclError:
                return res.failure(RTError(
                    node.attribute.start, node.attribute.end,
                    f"'{var_name}' has no attribute '{node.attribute.value}'",
                    context
                ))
            
        return res.success(result.copy().set_context(context).set_pos(node.start, node.end))


global_symbol_table = SymbolTable()
global_symbol_table.set('True', Number(1))
global_symbol_table.set('False', Number(0))
global_symbol_table.set('None', Variable(None))
global_symbol_table.set('rgb', BuiltInFunction('rgb'))

def run(filename, text, args={}):
    lexer = Lexer(filename, text)
    tokens, error = lexer.make_tokens()
    if error: return None, error

    if len(tokens) == 1: return '', None

    parser = Parser(tokens)
    ast = parser.parse()
    if ast.error: return None, ast.error

    interpreter = Interpreter()
    context = Context('<program>')

    for key, value in args.items():
        global_symbol_table.set(key, Variable(value))

    context.symbol_table = global_symbol_table

    result = interpreter.visit(ast.node, context)

    return result.value, result.error

