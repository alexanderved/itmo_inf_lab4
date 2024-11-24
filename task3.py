'''
m - any natural number >= 0

The implication is that the parser would automatically skip empty lines
unless stated otherwise.

---

space ::= #x20
newline ::= #xA
colon ::= ':'

indent(0) ::= empty
indent(n) ::= ' ' indent(n-1)

literal(n) ::= line-dict(n) | line-list(n) |
    multiline-string(n) | quoted-string(n) | string(n)

dict-key ::= [^-] string
dict-entry(n) ::= dict-key space* colon space* (
    space literal(n+1) |
    newline (
        indent(n+m+1) (dict(n+m+1) | literal(n+1)) |
        indent(n+m) list(n+m)
    )
)
dict(n) ::= dict-entry(n) (newline indent(n) dict-entry(n))*

list-entry-value(n, k) ::=
    (dict(n+k) | list(n+k) | literal(n))
list-entry(n) ::= '-' (
    indent(m+1) list-entry-value(n+1, m+1) |
    newline indent(n+m+1) list-entry-value(n+1, m)
)
list(n) ::= list-entry(n) (newline indent(n) list-entry(n))*

document ::= ('---' newline )? indent(m) (list(m) | dict(m)) (newline '...')?
file ::= document+
'''


import re


class FileBuffer:
    def __init__(self, filepath):
        self._file = open(filepath)
        self._curr_line = None
        self._offset = 0
        self._index = 0

        self.next()

    
    def closed(self):
        return self._file is None or self._file.closed


    def line_index(self):
        return self._index

    
    def line(self):
        if self._curr_line is None:
            return None

        return self._curr_line[self._offset:].rstrip()


    def full_line(self):
        if self._curr_line is None:
            return None

        return self._curr_line.rstrip()


    def next(self):
        try:
            self._curr_line = \
                re.fullmatch(r'(.*?)(?:#.*)?', next(self._file).rstrip())[1]

            self._index += 1
            self._offset = 0
        except:
            self._file.close()
            self._file = None

            self._curr_line = None

            self._index = -1
            self._offset = -1

        
    def skip(self):
        while self.full_line() is not None and len(self.full_line().strip()) == 0:
            self.next()


    def offset(self):
        return self._offset


    def add_offset(self, n):
        self._offset += n


    def __del__(self):
        if self._file is not None:
            self._file.close()

class YamlParser:
    GREATER_INDENT = 1
    LESS_INDENT = -1
    EQUAL_INDENT = 0


    def __init__(self):
        self._buf = None

    
    def parse(self, filepath):
        self._buf = FileBuffer(filepath)

        self._buf.skip()
        docs = []

        while not self._buf.closed():
            docs.append(self._parse_doc())

        del self._buf
        self._buf = None

        return docs

    
    def _handle_error(self, s):
        print(f'Error at line {self._buf.line_index()}: {s}')
        exit(1)


    def _indent_len(self):
        return len(self._buf.full_line()) - len(self._buf.full_line().lstrip())


    def _cmp_indent_len_to(self, n):
        if self._indent_len() > n:
            return self.GREATER_INDENT
        elif self._indent_len() < n:
            return self.LESS_INDENT
        else:
            return self.EQUAL_INDENT

    
    def _is_doc_start(self):
        return self._buf.full_line() == '---'


    def _is_doc_end(self):
        return self._buf.full_line() == '...'


    def _is_eod(self):
        return self._buf.full_line() is None or \
            self._is_doc_start() or self._is_doc_end()


    def _parse_doc(self):
        if self._is_doc_start():
            self._buf.next()
        self._buf.skip()

        doc = None
        if self._is_list_start():
            doc = self._parse_list(self._indent_len())
        elif self._is_dict_start():
            doc = self._parse_dict(self._indent_len())
        else:
            self._handle_error('Unknown document format')

        if self._is_doc_end():
            self._buf.next()
        self._buf.skip()

        return doc


    def _is_dict_start(self):
        return re.fullmatch(r'[ ]*[^-\s].*?:(?:[ ]+.*)?', self._buf.line()) is not None

    
    def _is_dict_key_valid(self, key):
        return ': ' not in key


    def _parse_dict_key(self, key):
        if not self._is_quoted(key) and not self._is_dict_key_valid(key):
            self._handle_error('A dictionary key must not contain \': \'')

        key = self._unqoute_string(key)

        return key


    def _parse_dict_entry(self, n):
        entry = re.fullmatch(r'[ ]*([^-\s].*?):', self._buf.line())
        if entry is not None:
            k = self._parse_dict_key(entry[1])
            v = None

            self._buf.next()
            self._buf.skip()

            indent_cmp = self._cmp_indent_len_to(n)

            if indent_cmp == self.GREATER_INDENT and self._is_dict_start():
                v = self._parse_dict(self._indent_len())
            elif indent_cmp != self.LESS_INDENT and self._is_list_start():
                v = self._parse_list(self._indent_len())
            elif indent_cmp == self.GREATER_INDENT and self._is_literal_start():
                v = self._parse_literal(n + 1)
            else:
                self._handle_error('A dictionary entry must not be empty')
                
            return (k, v)

        entry = re.fullmatch(r'([ ]*([^-\s].*?):[ ]+)(?:.*)?', self._buf.line())
        if entry is not None:
            k = self._parse_dict_key(entry[2])

            self._buf.add_offset(len(entry[1]))
            v = self._parse_literal(n + 1)

            return (k, v)

        self._handle_error('Unknown type of dictionary entry')


    def _parse_dict(self, n):
        entries = {}

        k, v = self._parse_dict_entry(n)
        entries[k] = v

        while not self._is_eod():
            match self._cmp_indent_len_to(n):
                case self.EQUAL_INDENT:
                    k, v = self._parse_dict_entry(n)
                    if k not in entries:
                        entries[k] = v
                    else:
                        self._handle_error(
                            'All keys in a dictionary must have different names')
                case self.GREATER_INDENT:
                    self._handle_error('Wrong indent')
                case self.LESS_INDENT:
                    break

        return entries


    def _is_list_start(self):
        return re.fullmatch(r'[ ]*-(?:[ ]+.*)?', self._buf.line()) is not None


    def _parse_list_entry(self, n):
        entry = re.fullmatch(r'[ ]*-', self._buf.line())
        if entry is not None:
            self._buf.next()
            self._buf.skip()

            indent_cmp = self._cmp_indent_len_to(n)

            v = None
            if indent_cmp == self.GREATER_INDENT:
                if self._is_dict_start():
                    v = self._parse_dict(self._indent_len())
                elif self._is_list_start():
                    v = self._parse_list(self._indent_len())
                elif self._is_literal_start():
                    v = self._parse_literal(n + 1)
            else:
                self._handle_error('A list entry must not be empty')
                
            return v

        entry = re.fullmatch(r'([ ]*-[ ]+)(?:.*)?', self._buf.line())
        if entry is not None:
            self._buf.add_offset(len(entry[1]))
            
            v = None
            if self._is_dict_start():
                v = self._parse_dict(self._buf.offset())
            elif self._is_list_start():
                v = self._parse_list(self._buf.offset())
            elif self._is_literal_start():
                v = self._parse_literal(n + 1)

            return v

        self._handle_error('Unknown type of list entry')


    def _is_list_entry(self):
        return self._buf.line().lstrip()[0] == '-'


    def _parse_list(self, n):
        entries = []
        entries.append(self._parse_list_entry(n))

        while not self._is_eod():
            match self._cmp_indent_len_to(n):
                case self.EQUAL_INDENT:
                    if not self._is_list_entry():
                        break

                    entries.append(self._parse_list_entry(n))
                case self.GREATER_INDENT:
                    self._handle_error('Wrong indent')
                case self.LESS_INDENT:
                    break

        return entries


    
    def _is_quoted(self, s):
        return re.fullmatch(r'\'.*\'|".*"', s.strip()) is not None


    def _unqoute_string(self, s):
        s = s.strip()

        if s.startswith('\''):
            if s.endswith('\''):
                return s[1:-1]
            else:
                self._handle_error('A string has no closing single quote')
        elif s.startswith('"'):
            if s.endswith('"'):
                # FIXME: Parse escape characters
                return s[1:-1]
            else:
                self._handle_error('A string has no closing double quote')
        else:
            return s


    def _is_literal_start(self):
        # FIXME
        return self._is_single_line_dict_start() or \
            self._is_single_line_list_start() or self._is_string_part()


    def _parse_literal(self, n):
        # FIXME
        if self._is_single_line_dict_start():
            return self._parse_single_line_dict(n)
        elif self._is_single_line_list_start():
            return self._parse_single_line_list(n)
        elif self._is_string_part():
            return self._parse_string(n)
        else:
            self._handle_error('Unknown literal type')


    def _is_single_line_list_start(self):
        return self._buf.line().strip().startswith('[')

    
    def _is_single_line_list(self, s):
        return s.startswith('[') and s.endswith(']')


    def _is_empty_single_line_list(self, s):
        return re.fullmatch(r'\[\s*\]', s) is not None

    
    def _parse_single_line_list(self, n):
        s = self._parse_string(n).strip()
        if self._is_single_line_list(s):
            if self._is_empty_single_line_list(s):
                return []

            values = [self._unqoute_string(value) for value in s[1:-1].split(',')]

            return list(map(str.strip, values))
        else:
            self._handle_error('A single line list does not have a closing square bracket')


    def _is_single_line_dict_start(self):
        return self._buf.line().strip().startswith('{')

    
    def _is_single_line_dict(self, s):
        return s.startswith('{') and s.endswith('}')


    def _is_empty_single_line_dict(self, s):
        return re.fullmatch(r'\{\s*\}', s) is not None


    def _parse_single_line_dict(self, n):
        s = self._parse_string(n).strip()
        if self._is_single_line_dict(s):
            if self._is_empty_single_line_dict(s):
                return {}

            items = [tuple(map(str.strip, item.split(':'))) for item in s[1:-1].split(',')]
            d = {}
            for k, v in items:
                d[self._parse_dict_key(k)] = self._unqoute_string(v).strip()

            return d
        else:
            self._handle_error('A single line list does not have a closing square bracket')


    def _is_string_part(self):
        return ': ' not in self._buf.line() and self._buf.line()[-1] != ':' \
            and not self._buf.line().startswith('- ')


    def _parse_string(self, n):
        string = self._buf.line().strip()
        if string == '>' or string == '|':
            self._buf.next()
            self._buf.skip()

        string = self._buf.line().strip()
        self._buf.next()
        self._buf.skip()

        while not self._is_eod():
            match self._cmp_indent_len_to(n):
                case self.LESS_INDENT:
                    break
                case _:
                    if not self._is_string_part():
                        break

                    string += ' ' + self._buf.line().strip()
                    self._buf.next()
                    self._buf.skip()

        return self._unqoute_string(string)


def _inner_dump_xml(data, lvl, f):
    if type(data) is str:
        f.write('    ' * lvl + data + '\n')
    elif type(data) is dict:
        for k, v in data.items():
            if v == {} or v == []:
                f.write('    ' * lvl + f'<{k}></{k}>\n')
            elif type(v) is str:
                f.write('    ' * lvl + f'<{k}>{v}</{k}>\n')
            else:
                f.write('    ' * lvl + f'<{k}>\n')
                _inner_dump_xml(v, lvl + 1, f)
                f.write('    ' * lvl + f'</{k}>\n')
    elif type(data) is list:
        for v in data:
            if v == {} or v == []:
                f.write('    ' * lvl + f'<value></value>\n')
            elif type(v) is str:
                f.write('    ' * lvl + f'<value>{v}</value>\n')
            else:
                f.write('    ' * lvl + '<value>\n')
                _inner_dump_xml(v, lvl + 1, f)
                f.write('    ' * lvl + '</value>\n')


def dump_xml(data, f):
    f.write('<?xml version="1.0" encoding="UTF-8"?>\n')
    f.write('<root>\n')
    for v in data:
        f.write('    ' + '<document>\n')
        _inner_dump_xml(v, 2, f)
        f.write('    ' + '</document>\n')
    f.write('</root>\n')


def main():
    with open('output/task3.xml', 'w') as out_file:
        dump_xml(YamlParser().parse('input/timetable_task3.yaml'), out_file)


if __name__ == '__main__':
    main()