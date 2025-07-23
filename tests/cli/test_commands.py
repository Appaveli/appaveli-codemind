import os
import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock

from appaveli_codemind.cli.commands import cli


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_info_command(runner):
    result = runner.invoke(cli, ["info"])
    assert result.exit_code == 0
    assert "Supported Languages" in result.output


@patch("version.__version__", "0.5.0")
@patch("version.__author__", "AppaveliTech")
@patch("version.__description__", "Test CLI agent")
def test_cli_version_command(runner):
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "AppaveliTech" in result.output
    assert "0.5.0" in result.output
    assert "Test CLI agent" in result.output

def test_cli_no_command_prints_logo(runner):
    result = runner.invoke(cli)
    assert result.exit_code == 0
    assert "Appaveli CodeMind" in result.output
    assert "Welcome to Appaveli CodeMind" in result.output


import os
import tempfile
import pytest
from click.exceptions import ClickException
from click.testing import CliRunner
from appaveli_codemind.cli.commands import cli


@pytest.fixture
def runner():
    return CliRunner()



def test_cli_missing_api_key_for_analyze(runner):
    with tempfile.NamedTemporaryFile(suffix=".java", delete=False) as temp:
        temp.write(b"public class Dummy {}")
        temp.flush()

        env = os.environ.copy()
        env.pop("OPENAI_API_KEY", None)

        with pytest.raises(ClickException) as exc_info:
            runner.invoke(cli, ["analyze", "--file", temp.name], env=env, obj={}, standalone_mode=False)

        assert "OpenAI API key is required" in str(exc_info.value)

    os.unlink(temp.name)