import csv


with open('input/timetable.yaml', 'r') as in_file, open('output/task5.csv', 'w') as out_file:
    writer = csv.writer(out_file, delimiter=';')

    columns = ['lesson', 'day', 'type', 'weeks',
        'start', 'end', 'teacher', 'building', 'room']
    writer.writerow(columns)

    lesson_info = dict.fromkeys(columns)

    for line in in_file:
        if 'day:' in line:
            continue
        elif 'name:' in line:
            lesson_info['day'] = line.strip().split(': ')[1]
        elif 'lesson:' in line:
            if None not in lesson_info.values():
                writer.writerow(lesson_info.values())
            lesson_info['lesson'] = line.strip()[2:].split(': ')[1]
        else:
            for c in columns:
                if c + ':' in line:
                    v = line.strip().split(': ')[1]

                    if (v.startswith('\'') and v.endswith('\'')) or \
                            (v.startswith('"') and v.endswith('"')):
                        v = v[1:-1]
                    elif v.startswith('[') and v.endswith(']'):
                        v = ','.join(v[1:-1].split(', '))

                    lesson_info[c] = v

    writer.writerow(lesson_info.values())
    
