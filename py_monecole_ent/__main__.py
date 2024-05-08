import argparse
import asyncio
import datetime
import logging
import re
import sys

import py_monecole_ent.client as mon_ecole_client

_LOGGER = logging.getLogger(__name__)


def cli(args):
    parser = argparse.ArgumentParser(
        prog="monecole", description="Simpe CLI for 'monecole'"
    )
    parser.add_argument("-u", "--username", required=True)
    parser.add_argument("-p", "--password", required=True)
    parser.add_argument(
        "--url",
        required=True,
        help="URL of the ENT (ex: https://monecole-ent.essonne.fr)",
    )
    parser.add_argument("-d", "--debug", action="store_true", default=False)

    subparsers = parser.add_subparsers(required=True, dest="command_name")
    parser_homeworks = subparsers.add_parser("homeworks")

    subparsers_homeworks = parser_homeworks.add_subparsers(
        required=False, dest="homeworks_command_name"
    )
    parser_homeworks_list = subparsers_homeworks.add_parser("list")
    parser_homeworks_get = subparsers_homeworks.add_parser("get")
    parser_homeworks_get.add_argument("homeworks_ids", nargs=1)
    parser_homeworks_get.add_argument("--today", action="store_true")
    parser_homeworks_get.add_argument("--tomorrow", action="store_true")
    parser_homeworks_get.add_argument("--thisweek", action="store_true")
    parser_homeworks_get.add_argument("--nextweek", action="store_true")

    args = parser.parse_args(args=args)

    asyncio.run(execute(args))


def strip_tags(text: str) -> str:
    return re.sub("<[^<]+?>", "", text)


def print_homework_list(homeworks_list: list):
    for h in homeworks_list:
        hw_date = datetime.datetime.fromtimestamp(h["modified"]["$date"] / 1000)
        print(
            f"""{h["title"]} - {h["_id"]} - by {h["name"]} - last modified {hw_date}"""
        )


def print_homeworks(homeworks: list):
    if not homeworks:
        print("No homeworks")
    for day in homeworks:
        date = datetime.date.fromisoformat(day["date"]).strftime("%A, %d of %B %Y")
        print(f"📖 {date}")
        for e in day["entries"]:
            print(f"""    📚 {e["title"]}: {strip_tags(e["value"])}""")


async def execute(args):
    _LOGGER.debug(f"URL: {args.url}")
    _LOGGER.debug(f"Username: {args.username}")
    _LOGGER.debug(f"Password: {args.password}")

    client = mon_ecole_client.AsyncClient(args.username, args.password, args.url)
    await client.login()

    result = None
    if args.command_name == "homeworks" and args.homeworks_command_name in [
        None,
        "list",
    ]:
        result = await client.homeworks_list()
        print_homework_list(result)
    elif args.command_name == "homeworks" and args.homeworks_command_name in ["get"]:
        homeworks_id = args.homeworks_ids[0]
        result = await client.homeworks(homeworks_id)

        start: datetime.date = datetime.date.min
        end: datetime.date = datetime.date.max
        today: datetime.date = datetime.date.today()
        if args.today:
            start = today
            end = start
        elif args.tomorrow:
            start = today + datetime.timedelta(days=1)
            end = start
        elif args.thisweek:
            start = today - datetime.timedelta(days=today.weekday())
            end = start + datetime.timedelta(days=6)
        elif args.nextweek:
            start = (
                today
                - datetime.timedelta(days=today.weekday())
                + datetime.timedelta(days=6)
            )
            end = start + datetime.timedelta(days=6)

        homeworks = []
        for h in result["data"]:
            hw_date = datetime.date.fromisoformat(h["date"])
            if start <= hw_date <= end:
                homeworks.append(h)
        print_homeworks(homeworks)

    await client.logout()


cli(sys.argv[1:])
