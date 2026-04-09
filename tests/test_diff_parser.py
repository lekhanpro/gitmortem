from gitmortem.diff_parser import parse_diff, summarize_diff_for_llm


def test_parse_diff_detects_rename_and_new_file() -> None:
    raw_diff = """diff --git a/src/old_name.py b/src/new_name.py
similarity index 93%
rename from src/old_name.py
rename to src/new_name.py
@@ -1,3 +1,3 @@
-old_value = True
+old_value = False
diff --git a/src/added.py b/src/added.py
new file mode 100644
@@ -0,0 +1,2 @@
+print("hello")
+print("world")
"""

    parsed = parse_diff(raw_diff)

    assert len(parsed) == 2
    assert parsed[0].is_renamed is True
    assert parsed[0].previous_filename == "src/old_name.py"
    assert parsed[0].filename == "src/new_name.py"
    assert parsed[1].is_new_file is True
    assert "status=renamed" in summarize_diff_for_llm(parsed)


def test_parse_diff_detects_deleted_file() -> None:
    raw_diff = """diff --git a/app/legacy.py b/app/legacy.py
deleted file mode 100644
@@ -1,2 +0,0 @@
-print("legacy")
-print("remove me")
"""

    parsed = parse_diff(raw_diff)

    assert len(parsed) == 1
    assert parsed[0].is_deleted_file is True
    assert parsed[0].filename == "app/legacy.py"
