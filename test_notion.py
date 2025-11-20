import os
from unittest.mock import MagicMock
from dotenv import load_dotenv
import notion_client


def _run_connection_check():
    """Helper: run the same logic the original script used and print results."""
    load_dotenv()
    notion_token = os.getenv("NOTION_TOKEN")
    page_id = os.getenv("PAGE_ID")

    notion = notion_client.Client(auth=notion_token)

    try:
        if page_id:
            page = notion.pages.retrieve(page_id=page_id)
            print("✅ Connection successful! Page ID:", page["id"])
        else:
            user = notion.users.me()
            print("✅ Connection successful! User:", user["name"])
    except Exception as e:
        print("❌ Error connecting to Notion API:", e)


def test_connection_with_page_id(monkeypatch, capsys):
    monkeypatch.setenv("NOTION_TOKEN", "dummy-token")
    monkeypatch.setenv("PAGE_ID", "page_123")

    mock_client = MagicMock()
    mock_client.pages.retrieve.return_value = {"id": "page_123"}

    monkeypatch.setattr(notion_client, "Client", lambda auth: mock_client)

    _run_connection_check()
    out = capsys.readouterr().out
    assert "Connection successful" in out
    assert "page_123" in out


def test_connection_without_page_id(monkeypatch, capsys):
    monkeypatch.setenv("NOTION_TOKEN", "dummy-token")
    # ensure PAGE_ID unset
    monkeypatch.delenv("PAGE_ID", raising=False)

    mock_client = MagicMock()
    mock_client.users.me.return_value = {"name": "Test User"}

    monkeypatch.setattr(notion_client, "Client", lambda auth: mock_client)

    _run_connection_check()
    out = capsys.readouterr().out
    assert "Connection successful" in out
    assert "Test User" in out


def test_connection_raises_exception(monkeypatch, capsys):
    monkeypatch.setenv("NOTION_TOKEN", "dummy-token")
    monkeypatch.setenv("PAGE_ID", "page_999")

    mock_client = MagicMock()
    mock_client.pages.retrieve.side_effect = Exception("network error")

    monkeypatch.setattr(notion_client, "Client", lambda auth: mock_client)

    _run_connection_check()
    out = capsys.readouterr().out
    assert "Error connecting to Notion API" in out
    assert "network error" in out
