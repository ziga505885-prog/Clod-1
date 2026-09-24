from gip.runtime.hermes_adapter import HermesAdapter

class FakeRuntime:
    def __init__(self):
        self.registered = {}
    def register_tool(self, name, handler):
        self.registered[name] = handler
    def run(self, task, context):
        return {"task": task, "context": context}

def test_adapter_is_runtime_neutral():
    runtime = FakeRuntime()
    adapter = HermesAdapter.from_runtime(runtime)
    def tool(args):
        return args
    adapter.register_tool("gip_read_docx", tool)
    assert runtime.registered["gip_read_docx"] is tool
    assert adapter.run("inspect", {"report_id": "R1"}) == {
        "task": "inspect", "context": {"report_id": "R1"}
    }

def test_adapter_requires_runtime_for_run():
    try:
        HermesAdapter().run("inspect", {})
    except RuntimeError as exc:
        assert "not configured" in str(exc)
    else:
        raise AssertionError("expected RuntimeError")

def test_empty_tool_name_rejected():
    try:
        HermesAdapter().register_tool("", lambda _: None)
    except ValueError:
        pass
    else:
        raise AssertionError("expected ValueError")
