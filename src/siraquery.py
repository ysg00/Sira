from argparse import ArgumentParser
from func import query_board, query_issue, query_project

from sys import stdin, stdout, stderr

issue_opts_list = ["assignee", "creator", "id", "key", "label", "priority",
                   "reporter", "type", "watcher"]

user_opts = ["assignee", "creater", "reporter", "watcher"]


def build_parser():
    query = ArgumentParser(
        prog="sira-query",
        description="TODO",
        epilog="TODO"
    )
    sub = query.add_subparsers(
        title="TODO",
        description="TODO",
        parser_class=ArgumentParser,
        help="TODO",
        dest="sub_command"
    )
    issue = sub.add_parser(
        "issue",
        prog="sira",
        description="TODO",
        epilog="TODO"
    )
    project = sub.add_parser(
        "project",
        prog="project",
        description="TODO",
        epilog="TODO"
    )
    board = sub.add_parser(
        "board",
        prog="board",
        description="TODO",
        epilog="TODO"
    )

    # add options in issue
    issue_opts = dict()
    for opt in issue_opts_list:
        issue_opts[opt] = issue.add_argument(
            "-{}".format(opt[0] if opt[0] != "l" else "L"),
            "--{}".format(opt),
            action="store",
            default=None,
            type=str,
            required=False,
            help="TODO",
            dest=opt
        )
    issue_opts["id"].type = int
    issue.add_argument(
        "constraint",
        action="store",
        nargs="?",
        default=None,
        type=str,
        help="TODO",
        metavar="CONSTR"
    )

    # add key in board
    board.add_argument(
        "-k", "--key",
        action="store",
        default=None,
        type=int,
        required=False,
        help="TODO",
        dest="key"
    )

    # add order and limit to each sub-command
    for sub_command in [issue, project, board]:
        sub_command.add_argument(
            "-l", "--limit",
            action="store",
            default=0,
            type=int,
            required=False,
            help="TODO",
            dest="limit"
        )
        sub_command.add_argument(
            "-o", "--order",
            action="store",
            default="recent",
            type=str,
            choices=["desc", "asc", "recent", "DESC", "ASC", "RECENT"],
            required=False,
            help="TODO",
            dest="order"
        )
    return query


def main():
    parser = build_parser()
    namespace = parser.parse_args()
    print(namespace)
    if not namespace.sub_command:
        parser.print_help()
        return
    if namespace.sub_command == "issue":
        kwargs = vars(namespace)
        jql = kwargs["constraint"] if kwargs["constraint"] else ""
        for element in kwargs:
            value = "currentUser()"\
                    if element in user_opts and kwargs[element] == "mine"\
                    else kwargs[element]
            if element not in (
                    "sub_command", "order", "limit", "constraint") and value:
                jql += " and {} = {}".format(element, value) if jql\
                       else "{} = {}".format(element, value)
        kwargs["constraint"] = jql
        print(query_issue(**kwargs))
    elif namespace.sub_command == "project":
        print(query_project(**vars(namespace)))
    elif namespace.sub_command == "board":
        print(query_board(**vars(namespace)))
    else:
        pass


if __name__ == '__main__':
    main()
