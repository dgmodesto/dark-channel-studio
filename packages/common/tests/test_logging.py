import json

import structlog

from dcs_common.logging import bind_context, clear_context, configure_logging


def test_json_logs_include_correlation_fields(capsys):
    configure_logging("INFO")
    clear_context()
    bind_context(correlation_id="abc")
    structlog.get_logger().info("hello")
    line = capsys.readouterr().out.strip().splitlines()[-1]
    data = json.loads(line)
    assert data["event"] == "hello"
    assert data["correlation_id"] == "abc"
    for key in ("run_id", "video_id", "channel_id"):
        assert key in data and data[key] is None
