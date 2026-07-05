# CSV Upload Drag-and-Drop Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a sidebar popover with native drag-and-drop CSV upload to the Streamlit dashboard.

**Architecture:** Pure Streamlit — a `st.popover` in the sidebar contains a `st.file_uploader` (built-in drag-and-drop) and an "Apply" button. On apply, uploaded files are saved to `csv/`, cache is cleared, and the app reruns. No changes to `pipeline.py`.

**Tech Stack:** Streamlit (no new dependencies)

## Global Constraints

- `streamlit>=1.29` for `st.popover`
- No changes to `pipeline.py`
- Follow existing code style in `app.py` (type hints, `_` prefix for private helpers)

---

### Task 1: Add upload helper function and popover UI

**Files:**
- Modify: `app.py` (add function + integrate into `main()`)

**Interfaces:**
- Produces: `_save_uploaded_files(uploaded_files: list) -> tuple[int, list[str]]` — saves files to `csv/`, returns (count_saved, error_messages)

- [ ] **Step 1: Add `import os` at the top of `app.py`**

```python
import os
```

Insert after line 1 (`from datetime import datetime`).

- [ ] **Step 2: Add `_save_uploaded_files` helper function**

Insert this function somewhere before `main()` (e.g., after `_filter_by_months` around line 24):

```python
def _save_uploaded_files(uploaded_files: list) -> tuple[int, list[str]]:
    os.makedirs("csv", exist_ok=True)
    saved = 0
    errors = []
    for f in uploaded_files:
        try:
            with open(os.path.join("csv", f.name), "wb") as out:
                out.write(f.getbuffer())
            saved += 1
        except Exception as e:
            errors.append(str(e))
    return saved, errors
```

- [ ] **Step 3: Insert the CSV upload popover in `main()`**

After line 425 (`st.sidebar.header("Steuerung")`) and before line 426 (`chart_type, selected_months, selected_categories = render_sidebar(expenses)`), insert:

```python
    with st.sidebar.popover("📁 CSV hochladen"):
        uploaded_files = st.file_uploader(
            "DKB-CSV-Dateien hier ablegen",
            type="csv",
            accept_multiple_files=True,
            key="csv_uploader",
        )
        if uploaded_files:
            st.caption(f"{len(uploaded_files)} Datei(en) ausgewählt")
            for f in uploaded_files:
                st.text(f"• {f.name}")
        if st.button("Anwenden", type="primary", use_container_width=True):
            if not uploaded_files:
                st.warning("Bitte wähle mindestens eine CSV-Datei aus.")
            else:
                saved, errors = _save_uploaded_files(uploaded_files)
                if saved > 0:
                    st.success(f"{saved} Datei(en) gespeichert nach csv/.")
                for err in errors:
                    st.error(f"Fehler: {err}")
                if saved > 0:
                    st.cache_data.clear()
                    st.rerun()
```

- [ ] **Step 4: Verify the app starts without errors**

Run: `streamlit run app.py`

Expected: App starts, sidebar shows "📁 CSV hochladen" button below "Steuerung". Clicking opens a popover with a file upload zone and Apply button.

- [ ] **Step 5: Run existing tests to confirm no regressions**

Run: `python -m pytest tests/ -v`

Expected: All tests pass.

- [ ] **Step 6: Commit**

```bash
git add app.py
git commit -m "feat: add CSV drag-and-drop upload via sidebar popover"
```

### Task 2: Add tests for `_save_uploaded_files`

**Files:**
- Modify: `tests/test_app.py`
- No files created

**Interfaces:**
- Consumes: `_save_uploaded_files(uploaded_files: list) -> tuple[int, list[str]]` from Task 1

- [ ] **Step 1: Add import for the new function**

Add `_save_uploaded_files` to the existing import on line 2 of `test_app.py`:

```python
from app import filter_expenses, filter_income, _save_uploaded_files
```

- [ ] **Step 2: Write test for successful file save**

```python
def test_save_uploaded_files_success(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from streamlit.runtime.uploaded_file_manager import UploadedFile
    import io
    fake = UploadedFile("test.csv", b"a,b,c\n1,2,3", 7, io.BytesIO(b"a,b,c\n1,2,3"))
    saved, errors = _save_uploaded_files([fake])
    assert saved == 1
    assert errors == []
    assert os.path.exists("csv/test.csv")
    with open("csv/test.csv") as f:
        assert f.read() == "a,b,c\n1,2,3"
```

- [ ] **Step 3: Write test for save error handling**

```python
def test_save_uploaded_files_error(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    from streamlit.runtime.uploaded_file_manager import UploadedFile
    import io
    # Create a scenario where the file can't be written (e.g., csv/ is a file)
    with open("csv", "w") as f:
        f.write("not a directory")
    fake = UploadedFile("test.csv", b"data", 4, io.BytesIO(b"data"))
    saved, errors = _save_uploaded_files([fake])
    assert saved == 0
    assert len(errors) >= 1
```

- [ ] **Step 4: Write test for empty input**

```python
def test_save_uploaded_files_empty():
    saved, errors = _save_uploaded_files([])
    assert saved == 0
    assert errors == []
```

- [ ] **Step 5: Run tests**

Run: `python -m pytest tests/ -v`

Expected: All 10+ tests pass (7 original + 3 new).

- [ ] **Step 6: Commit**

```bash
git add tests/test_app.py
git commit -m "test: add tests for _save_uploaded_files"
```
