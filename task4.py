import time

from task0 import main as task0
from task1 import main as task1
from task2 import main as task2
from task3 import main as task3

def benchmark(name, task):
    t = 0
    n = 1000

    for i in range(n):
        start_time = time.time_ns()
        task()
        t += time.time_ns() - start_time

    print(f'{name}: {t // n}ns')


benchmark('Обязательное задание', task0)
benchmark('Дополнительное задание 1', task1)
benchmark('Дополнительное задание 2', task2)
benchmark('Дополнительное задание 3', task3)