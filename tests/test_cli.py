"""Tests for the medu command (cli.py)."""

import pytest

from medu import __version__, cli


@pytest.fixture(autouse=True)
def no_network(monkeypatch):
    monkeypatch.setenv("MEDU_NO_UPDATE_CHECK", "1")
    monkeypatch.setenv("NO_COLOR", "1")


def run(capsys, *args):
    code = cli.main(list(args))
    return code, capsys.readouterr().out


@pytest.mark.parametrize("flag", ["-v", "--version", "version"])
def test_version(capsys, flag):
    code, out = run(capsys, flag)
    assert code == 0 and __version__ in out


@pytest.mark.parametrize("flag", ["commands", "--commands", "-c"])
def test_commands_list(capsys, flag):
    code, out = run(capsys, flag)
    assert code == 0
    for cmd in ("medu translate", "medu run", "medu check", "medu upgrade", "medu downgrade"):
        assert cmd in out


def test_help(capsys):
    code, out = run(capsys, "--help")
    assert code == 0 and "Help and contact" in out


def test_translate_file(capsys):
    code, out = run(capsys, "-q", "translate", "samples/sentences.mdt")
    assert code == 0 and "I am sleeping." in out and "Translated 13 sentences" in out


def test_file_by_extension(capsys):
    code, out = run(capsys, "-q", "samples/sentences.mdt")
    assert code == 0 and "English" in out


def test_check_ok_and_error(capsys):
    assert run(capsys, "check", "samples/sentences.mdt")[0] == 0
    code, out = run(capsys, "check", "samples/errors/no_verb.mdt")
    assert code == 1 and "E202" in out


def test_run_waits_for_mode1(capsys, tmp_path):
    prog = tmp_path / "p.med"
    prog.write_text('x = 1\n', encoding="utf-8")
    code, out = run(capsys, "-q", "run", str(prog))
    assert code == 1 and "Medu 2.0" in out


def test_unknown_command_suggests(capsys):
    code, out = run(capsys, "translat")
    assert code == 1 and "did you mean: medu translate" in out


def test_missing_file(capsys):
    code, out = run(capsys, "translate", "nope.mdt")
    assert code == 1 and "cannot open" in out
