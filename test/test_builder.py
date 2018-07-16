"""A simple script to build up unit test module.
Please modifiy directory, file_name, and other constants before using in your
own projects.
"""

directory = "test"
file_name = "test_cases.md"


with open("/".join([directory, file_name]), "r") as f:
    lines = f.readlines()

header = \
"""import unittest
import sys
from subprocess import run

src_path = "src/"
sys.path.insert(0, src_path)
from sira import build_parser
#########################################

"""

footer = \
"""
def main():
    unittest.main()

if __name__ == '__main__':
    main()
"""

file_name = "test_001.py"
with open("/".join([directory, file_name]), "w") as f:
    f.write(header)
    index = 0
    class_index = 0
    for line in lines:
        if line.startswith("#"):
            f.write(line + "\n")
        if line.startswith("`"):
            f.write("    def test_{}(self):\n".format(index))
            f.write(
                '        namespace = self.parser.parse_args("{}")\n'.format(
                    line[1:-2]
                )
            )
            f.write("        kwargs = vars(namespace)\n\n")
            index += 1
        elif line.startswith("-") or line.startswith("##"):
            f.write("class Test_{}(unittest.TestCase):\n".format(class_index))
            f.write("    def setUp(self):\n")
            f.write("        self.parser = build_parser()\n\n")
            class_index += 1

    f.write(footer)

for line in lines:
    if line.startswith("`"):
        print(line[1:-2])