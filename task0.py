def get_indent(s):
    '''
    Возвращает отступ элемента.
    '''

    indent_len = 0
    while s[indent_len] == ' ':
        indent_len += 1

    if s[indent_len:indent_len + 2] == '- ':
        indent_len += 1
    else:
        return s[:indent_len]

    while s[indent_len] == ' ':
        indent_len += 1

    return s[:indent_len]


def get_nb_spaces(indent):
    '''
    Возвращает число пробелов перед элементом.
    '''

    return len(indent) - len(indent.lstrip())


def is_dict_entry(line):
    '''
    Проверяет, является ли строка элементом словаря.
    '''

    return ': ' in line or line.rstrip().endswith(':')


def is_list_entry(indent):
    '''
    Проверяет, является ли строка с даннным отступом элементом списка.
    '''
    return indent.strip().startswith('-')


def indent_exists(indent):
    '''
    Проверяет, встречались ли элементы с данным отступом.
    '''
    
    global indents, opened, out_file

    for other in indents:
        if get_nb_spaces(indent) == get_nb_spaces(other) and \
                is_list_entry(indent) == is_list_entry(other):
            return True

    return False


def parse_string(s):
    if (s[0] == '\'' and s[-1] == '\'') or (s[0] == '"' and s[-1] == '"'):
        return s[1:-1]

    return s


def paste_list_entry(line):
    '''
    Вставляет в выходной файл элемент списка.
    '''

    global indents, opened, out_file

    indent = get_indent(line)
    value = line[len(indent):].strip()

    if value[0] == '[' and value[-1] == ']':
        values = map(str.strip, value[1:-1].split(','))
        for v in map(parse_string, values):
            out_file.write('    ' * (len(opened) + 1) + f'<value>{v}</value>\n')
    else:
        out_file.write('    ' * (len(opened) + 1) + f'{parse_string(value)}\n')


def paste_element(key, value):
    '''
    Вставляет в выходной файл элемент XML, полученный из элемента словаря YAML.
    '''

    global indents, opened, out_file

    if value[0] == '[' and value[-1] == ']':
        if len(value[1:-1].strip()) == 0:
            out_file.write('    ' * (len(opened) + 1) + f'<{key}></{key}>\n')
        else:
            values = list(map(str.strip, value[1:-1].split(',')))

            out_file.write('    ' * (len(opened) + 1) + f'<{key}>\n')
            for v in map(parse_string, values):
                out_file.write('    ' * (len(opened) + 2) + f'<value>{v}</value>\n')
            out_file.write('    ' * (len(opened) + 1) + f'</{key}>\n')
    else:
        out_file.write('    ' * (len(opened) + 1) + \
            f'<{key}>{parse_string(value)}</{key}>\n')


def open_element(elem, indent):
    '''
    Открывает элемент XML, который будет закрыт при нахождении другого элемента
    с данным отступом или при достижении конца файла.
    '''

    global indents, opened, out_file

    opened.append((elem, indent))
    out_file.write('    ' * len(opened) + f'<{elem}>\n')


def close_elements(indent):
    '''
    Закрывает все последние элементы XML с данным отступом.
    '''

    global indents, opened, out_file

    while len(opened) > 0 and opened[-1][1] == indent:
        out_file.write('    ' * len(opened) + f'</{opened[-1][0]}>\n')
        opened.pop()


def is_line_skippable(line):
    line = line.rstrip()

    return line == '---' or line == '...' or line == ''


indents = []
opened = []

out_file = None


def main():
    global indents, opened, out_file

    with open('input/timetable.yaml', 'r') as in_file, \
        open('output/task0.xml', 'w') as out_file:
        out_file.write('<?xml version="1.0" encoding="UTF-8"?>\n')
        out_file.write('<root>\n')

        for i, line in enumerate(in_file.readlines()):
            if is_line_skippable(line):
                continue

            indent = get_indent(line)
            
            '''
            Проверяет, существует ли уровень, на котором может быть размещен
            элемент XML с данным оступом.
            '''
            if not indent_exists(indent) and \
                    len(indents) != 0 and get_nb_spaces(indent) < get_nb_spaces(indents[-1]):
                print(f'Wrong indentation at line {i + 1}.')
                exit(1)

            '''
            Закрывает предыдущий элемент XML с данным отступом и
            все вложенные в него элементы. 
            '''
            while indent_exists(indent):
                close_elements(indents[-1])
                indents.pop()

            '''
            Открывет элемент XML.
            '''
            indents.append(indent)

            if is_list_entry(indent):
                open_element('value', indent)

            if is_dict_entry(line):
                key, value = map(str.strip, line[len(indent):].split(':', 1))
            
                if value == '':
                    open_element(key, indent)
                else:
                    paste_element(key, value)
            else:
                paste_list_entry(line)

        '''
        Закрывает все оставшиеся элементы XML.
        '''
        while len(indents) != 0:
            close_elements(indents[-1])
            indents.pop()

        out_file.write('</root>\n')

    indents = []
    opened = []

    out_file = None


if __name__ == '__main__':
    main()