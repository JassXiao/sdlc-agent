import re
import json

def _extract_relevant_errors(log_text: str) -> str:
    failures = []

    # Best-effort framework detection
    framework = "unknown"
    if "pytest" in log_text.lower() or "=== FAILURES ===" in log_text:
        framework = "pytest"
    elif "Traceback (most recent call last):" in log_text and ("FAIL:" in log_text or "ERROR:" in log_text):
        framework = "unittest"
    elif "--- FAIL:" in log_text and ".go:" in log_text:
        framework = "go test"

    # Normalize newlines
    log_text = log_text.replace("\r\n", "\n")

    # Filter out known warning blocks and warning lines
    lines = log_text.split("\n")
    cleaned_lines = []
    in_warning_summary = False
    for line in lines:
        # Pytest warning summary detection
        if "=== warnings summary ===" in line or "--- warnings summary ---" in line:
            in_warning_summary = True
            continue
        if in_warning_summary and (line.startswith("===") or line.startswith("---")) and "warnings" not in line:
            in_warning_summary = False

        if not in_warning_summary:
            # Skip standalone warning lines
            if re.search(r'(?:DeprecationWarning|UserWarning|PytestWarning|Warning|WARNING):', line):
                continue
            cleaned_lines.append(line)

    cleaned_log = "\n".join(cleaned_lines)

    # 1. PYTEST EXTRACTION
    # Pytest failure blocks are separated by lines like:
    # ___________________________ test_name ___________________________
    # Using non-greedy matching (+?) to avoid capturing the trailing underscores as part of the test name.
    pytest_blocks = re.split(r'\n_+\s*([a-zA-Z0-9_\[\]\-\.\:\/ ]+?)\s*_+\n', "\n" + cleaned_log)
    if len(pytest_blocks) > 1:
        for i in range(1, len(pytest_blocks), 2):
            if len(failures) >= 5:
                break
            test_name = pytest_blocks[i].strip()
            block_content = pytest_blocks[i+1]

            # Extract file path and line number
            file_path = ""
            line_num = None

            # Try pattern: test_file.py:10: AssertionError
            file_line_match = re.search(r'([a-zA-Z0-9_\-\./\\]+\.py):(\d+):', block_content)
            if file_line_match:
                file_path = file_line_match.group(1)
                line_num = int(file_line_match.group(2))
            else:
                # Try pattern: File "test_file.py", line 10
                file_line_match2 = re.search(r'File "([^"]+)", line (\d+)', block_content)
                if file_line_match2:
                    file_path = file_line_match2.group(1)
                    line_num = int(file_line_match2.group(2))

            # Extract assertion/error message
            err_lines = []
            for line in block_content.split("\n"):
                stripped = line.strip()
                if line.startswith("E   ") or line.startswith("E "):
                    err_lines.append(line[2:].strip())
                elif stripped.startswith("AssertionError:") or stripped.startswith("ValueError:") or stripped.startswith("TypeError:"):
                    err_lines.append(stripped)

            message = " ".join(err_lines).strip()
            if not message:
                # Fallback to lines starting with '>'
                fallback_lines = []
                for line in block_content.split("\n"):
                    if line.startswith(">"):
                        fallback_lines.append(line.strip())
                message = " ".join(fallback_lines).strip()

            failures.append({
                "test_name": test_name,
                "file": file_path,
                "line": line_num,
                "message": message or "Assertion failed"
            })
            if framework == "unknown":
                framework = "pytest"

    # 2. UNITTEST EXTRACTION
    if len(failures) < 5:
        # Match FAIL: test_something or ERROR: test_something blocks
        matches = re.finditer(r'^(?:FAIL|ERROR):\s+([a-zA-Z0-9_]+)[^\n]*\n(.*?)(?=\n(?:FAIL|ERROR|={5,}|-{5,})|\Z)', cleaned_log, re.MULTILINE | re.DOTALL)
        for match in matches:
            if len(failures) >= 5:
                break
            test_name = match.group(1).strip()
            block_content = match.group(2)

            # Find last traceback line for file/line
            file_line_matches = re.findall(r'File "([^"]+)", line (\d+)', block_content)
            file_path = ""
            line_num = None
            if file_line_matches:
                file_path, line_str = file_line_matches[-1]
                line_num = int(line_str)

            # The message is usually the last non-empty line of the block
            block_lines = [l.strip() for l in block_content.strip().split("\n") if l.strip()]
            message = ""
            if block_lines:
                message = block_lines[-1]

            failures.append({
                "test_name": test_name,
                "file": file_path,
                "line": line_num,
                "message": message or "Assertion failed"
            })
            if framework == "unknown":
                framework = "unittest"

    # 3. GO TEST EXTRACTION
    if len(failures) < 5:
        # Parse Go failures
        go_blocks = re.split(r'\n--- FAIL:\s+([a-zA-Z0-9_]+)[^\n]*\n', "\n" + cleaned_log)
        if len(go_blocks) > 1:
            for i in range(1, len(go_blocks), 2):
                if len(failures) >= 5:
                    break
                test_name = go_blocks[i].strip()
                block_content = go_blocks[i+1]

                # Find all occurrences of file:line: message in this block
                matches = re.findall(r'^\s*([^\s:]+\.go):(\d+):\s*(.*)$', block_content, re.MULTILINE)
                if matches:
                    for file_path, line_str, msg in matches:
                        if len(failures) >= 5:
                            break
                        failures.append({
                            "test_name": test_name,
                            "file": file_path,
                            "line": int(line_str),
                            "message": msg.strip()
                        })
                else:
                    # Fallback if no file/line matched
                    failures.append({
                        "test_name": test_name,
                        "file": "",
                        "line": None,
                        "message": block_content.strip()
                    })
            if framework == "unknown":
                framework = "go test"

    result = {
        "framework": framework,
        "failures": failures[:5]
    }
    return json.dumps(result, indent=2, ensure_ascii=False)
