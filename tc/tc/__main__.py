import logging
import re
import sys
from tc import Interpreter


def repl():
    interpreter = Interpreter()

    try:
        while True:
            # Read program from input.
            code = ''

            try:
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
            except Exception as e:
                logging.error(e)

    except KeyboardInterrupt:
        pass


def interpret(input_str):
    interpreter = Interpreter()
    interpreter.run(input_str, opt=True)


def main():
    if len(sys.argv) == 1:
        repl()
    else:
        file = sys.argv[1]
        with open(file, 'r') as input_f:
            interpret(input_f.read())


if __name__ == '__main__':
    main()
