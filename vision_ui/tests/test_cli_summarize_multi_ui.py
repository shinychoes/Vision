import tempfile
from vision_ui.cli import main


def test_cli_summarize_multi_minimal(capsys):
    text = "Hello world. This is a test." * 20
    with tempfile.NamedTemporaryFile("w+", delete=False, encoding="utf-8") as fh:
        fh.write(text)
        path = fh.name

    argv = ["summarize-multi", "--file", path, "--profiles", "phone,laptop", "--format", "compact"]
    main(argv)
    captured = capsys.readouterr()
    assert "phone.headline" in captured.out or "phone.one_screen" in captured.out
