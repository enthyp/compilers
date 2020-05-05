import re
from tc import Interpreter


def repl():
    interpreter = Interpreter()

    while True:
        # Read program from input.
        code = ''
        while True:
            try:
                prompt = 'calc> ' if not code else '... '
                s = input(prompt)
            except EOFError:
                print('EOF')
                break
            if not s.strip():
                continue
               
            code += s.strip()
            if not re.match(r'\s', s[-1]):
                break

        interpreter.run(code)
        code = ''


if __name__ == '__main__':
    repl()

