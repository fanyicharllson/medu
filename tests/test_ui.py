"""Tests for the terminal look (banner, colours)."""

from medu import __version__, ui
from medu.errors import MeduError

ESC = "\033["


def test_banner_shows_name_version_and_language():
    ui.setup(color=False)
    text = ui.banner("medumba")
    assert "|_|  |_|_____|____/ \\___/" in text
    assert f"v{__version__}" in text
    assert "Mə̀dʉ̂mbɑ̀ → English" in text
    assert ESC not in text


def test_colours_only_when_enabled():
    ui.setup(color=False)
    assert ui.result("Emperor") == "Emperor"
    ui.setup(color=True)
    assert ESC in ui.result("Emperor")
    ui.setup(color=False)


def test_coloured_error_keeps_same_text():
    err = MeduError("E101", "unknown word 'zii'", 1, 4, hint="did you mean 'zi'?")
    plain = err.format("s.mdt", "mə zii.")
    coloured = err.format("s.mdt", "mə zii.", color=True)
    assert ESC not in plain and ESC in coloured
    import re
    assert re.sub(r"\033\[[0-9;]*m", "", coloured) == plain


def test_header_one_line():
    ui.setup(color=False)
    assert ui.header("medumba", "run") == f"Medu v{__version__} · run · Mə̀dʉ̂mbɑ̀"


def test_version_and_help_text():
    ui.setup(color=False)
    assert __version__ in ui.version_text()
    assert "CharlseEmpire Tech" in ui.version_text()
    text = ui.help_text(prompt_mode=True)
    for word in ("cls", "medu --version".split()[0], "issues", "mə kə̀ jʉ"):
        assert word in text


def test_command_line_flags(capsys):
    from medu import mode2
    assert mode2.main(["-v"]) == 0
    assert __version__ in capsys.readouterr().out
    assert mode2.main(["--help"]) == 0
    assert "Help and contact" in capsys.readouterr().out
    assert mode2.main(["-q", "translate", "samples/sentences.mdt"]) == 0
    assert "I am sleeping." in capsys.readouterr().out
    assert mode2.main(["no_such_file.mdt"]) == 1


def test_welcome_name_from_installer(tmp_path, monkeypatch):
    ui.setup(color=False)
    monkeypatch.setenv("MEDU_CONFIG_DIR", str(tmp_path))
    assert "Welcome" not in ui.banner()
    (tmp_path / "config.json").write_text('\ufeff{"name": "Joy"}', encoding="utf-8")
    assert "Welcome, Joy!" in ui.banner()
    assert "Welcome" not in ui.banner(hint=False)      # files: no greeting


def test_version_comparison():
    from medu import updater
    assert updater.is_newer("1.1.0", "1.0.0")
    assert updater.is_newer("v2.0.0", "1.9.9")
    assert not updater.is_newer("1.0.0", "1.0.0")
    assert not updater.is_newer("0.9.0", "1.0.0")


def test_release_assets_prefer_installer():
    from medu import updater
    r = updater._from_api({"tag_name": "v1.1.0", "body": "notes", "html_url": "u", "assets": [
        {"name": "medu.exe", "browser_download_url": "https://x/medu.exe"},
        {"name": "Medu-Setup-1.1.0.exe", "browser_download_url": "https://x/setup.exe"}]})
    assert r.version == "1.1.0" and r.setup_url.endswith("setup.exe") and r.exe_url


def test_upgrade_from_source_says_git_pull(capsys):
    from medu import updater
    assert updater.install() == 1
    assert "git pull" in capsys.readouterr().out
