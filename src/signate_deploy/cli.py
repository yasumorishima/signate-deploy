"""CLI entry point for signate-deploy."""

import click

from signate_deploy import __version__
from signate_deploy.commands.init_repo import init_repo
from signate_deploy.commands.init import init
from signate_deploy.commands.submit import submit
from signate_deploy.commands.download import download
from signate_deploy.commands.setup_token import setup_token
from signate_deploy.commands.competition_list import competition_list
from signate_deploy.commands.task_list import task_list
from signate_deploy.commands.file_list import file_list


@click.group()
@click.version_option(version=__version__)
def main():
    """GitHub Actions経由でSIGNATEコンペを自動化するCLIツール

    データDL → 学習 → 提出 の一気通貫パイプラインをセットアップします。
    """
    pass


main.add_command(init_repo)
main.add_command(init)
main.add_command(submit)
main.add_command(download)
main.add_command(setup_token)
main.add_command(competition_list)
main.add_command(task_list)
main.add_command(file_list)
