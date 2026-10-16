import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# 将 data/plugins 目录加入 sys.path，以便以包的形式导入插件
plugins_dir = Path(__file__).resolve().parent.parent.parent
if str(plugins_dir) not in sys.path:
    sys.path.insert(0, str(plugins_dir))

from astrbot_plugin_new_qq_tools.main import QQToolsPlugin  # noqa: E402

import astrbot.api.message_components as Comp  # noqa: E402


@pytest.fixture
def plugin():
    context = MagicMock()
    config = {
        "context_enhance": {
            "show_message_id": True,
            "skip_msg_id_prefixes": [],
        },
        "compatibility": {
            "delay_append_msg_id": False,
        },
        "reply_quote": {
            "enhance_reply_quote": False,
        },
        "file_info": {
            "show_file_info": False,
        },
    }
    with patch("asyncio.create_task"):
        p = QQToolsPlugin(context, config)
        return p


@pytest.mark.asyncio
async def test_empty_event_is_stopped_and_not_injected(plugin):
    """测试协议端推送的纯空消息事件被正确阻断，且不会注入 MSG_ID"""
    event = MagicMock()
    event.message_str = ""
    event.message_obj = MagicMock()
    event.message_obj.message_id = "1713508323"
    event.message_obj.message = []
    event.message_obj.raw_message = {
        "post_type": "message",
        "message_type": "private",
        "raw_message": "",
        "message": [],
    }
    event.get_session_id.return_value = "2114014119"
    event.get_sender_id.return_value = "2114014119"
    event.get_sender_name.return_value = "User"
    event.stop_event = MagicMock()

    await plugin._on_message_internal(event)

    # 验证被阻断
    event.stop_event.assert_called_once()
    # 验证未被污染注入 MSG_ID
    assert "MSG_ID" not in event.message_str
    assert len(event.message_obj.message) == 0


@pytest.mark.asyncio
async def test_normal_text_message_is_processed(plugin):
    """测试普通文本消息正常处理并注入 MSG_ID"""
    event = MagicMock()
    event.message_str = "把例题.md发我"
    event.message_obj = MagicMock()
    event.message_obj.message_id = "977358449"
    event.message_obj.message_str = "把例题.md发我"
    plain_comp = Comp.Plain("把例题.md发我")
    event.message_obj.message = [plain_comp]
    event.message_obj.raw_message = {
        "post_type": "message",
        "message": [{"type": "text", "data": {"text": "把例题.md发我"}}],
    }
    event.get_session_id.return_value = "2114014119"
    event.get_sender_id.return_value = "2114014119"
    event.get_sender_name.return_value = "User"
    event.stop_event = MagicMock()

    await plugin._on_message_internal(event)

    # 验证未被阻断
    event.stop_event.assert_not_called()
    # 验证注入了 MSG_ID
    assert "[MSG_ID:977358449]" in event.message_str


@pytest.mark.asyncio
async def test_image_only_message_is_processed(plugin):
    """测试纯图片消息正常处理并注入 MSG_ID"""
    event = MagicMock()
    event.message_str = ""
    event.message_obj = MagicMock()
    event.message_obj.message_id = "888888"
    event.message_obj.message_str = ""
    img_comp = Comp.Image(file="test.png")
    event.message_obj.message = [img_comp]
    event.message_obj.raw_message = {
        "post_type": "message",
        "message": [{"type": "image"}],
    }
    event.get_session_id.return_value = "2114014119"
    event.get_sender_id.return_value = "2114014119"
    event.get_sender_name.return_value = "User"
    event.stop_event = MagicMock()

    await plugin._on_message_internal(event)

    # 验证未被阻断
    event.stop_event.assert_not_called()
    # 验证注入了 MSG_ID
    assert "[MSG_ID:888888]" in event.message_str
