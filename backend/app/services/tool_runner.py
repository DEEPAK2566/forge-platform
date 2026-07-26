"""
Tool Runner — generic executor for any FORGE tool.

This file knows NOTHING about specific tools (GitHub, Jira, Databricks etc).
It only:
  1. Parses the JSON input from the execution engine
  2. Sets ALL JSON keys as environment variables (uppercased)
  3. Matches run() parameters by EXACT name from JSON
  4. Calls run() with whatever matched
  5. Restores env vars after

Each tool's run() method is responsible for reading its own env vars
and handling its own parameter fallbacks. The tool_runner never changes
when you add a new tool.
"""

import os
import json
import traceback
import inspect


def run_tool(tool_record, input_text: str) -> str:
    """
    Execute a tool's Python code with the provided JSON input.

    tool_record : SQLAlchemy Tool object (.code, .tool_class, .name)
    input_text  : JSON string from execution engine
                  Contains all workflow variables + 'content' key

    Returns the tool's string output or a JSON error message.
    """
    if not tool_record or not tool_record.code:
        return json.dumps({
            "error":   True,
            "message": f"Tool '{getattr(tool_record, 'name', '?')}' has no code saved."
        })

    tool_class_name = (tool_record.tool_class or "").strip()
    code            = tool_record.code

    print(f"\n[ToolRunner] ── Executing: {tool_record.name} (class: {tool_class_name})")

    # ── Step 1: Parse JSON input ──────────────────────────────────────────
    input_data = {}
    try:
        parsed = json.loads(input_text.strip())
        if isinstance(parsed, dict):
            input_data = {k: str(v).strip() for k, v in parsed.items() if v is not None}
        print(f"[ToolRunner] Input keys: {list(input_data.keys())}")
    except Exception:
        # Not JSON — treat as plain text
        input_data = {"content": input_text.strip(), "query": input_text.strip()}
        print(f"[ToolRunner] Input is plain text, wrapped as content/query")

    # ── Step 2: Set ALL input keys as env vars ────────────────────────────
    # We uppercase them so tools can read os.environ.get("GITHUB_TOKEN"),
    # os.environ.get("JIRA_BASE_URL") etc without any mapping in tool_runner.
    #
    # Example JSON: {"github_token": "ghp_...", "github_repo": "org/repo"}
    # Env vars set: GITHUB_TOKEN=ghp_..., GITHUB_REPO=org/repo
    #
    # The tool's own run() method then does:
    #   token = token or os.environ.get("GITHUB_TOKEN", "")
    #   repo  = repo  or os.environ.get("GITHUB_REPO",  "")
    #
    # This is the ONLY mechanism — tool_runner never knows about specific keys.

    old_env_values = {}
    for key, value in input_data.items():
        env_key = key.upper()
        old_env_values[env_key] = os.environ.get(env_key)
        os.environ[env_key] = value
        display = (value[:4] + "****") if len(value) > 8 else "****"
        print(f"[ToolRunner] ENV set: {env_key} = {display}")

    try:
        # ── Step 3: Execute tool code ─────────────────────────────────────
        namespace = {"__builtins__": __builtins__, "os": os}

        # Pre-load commonly needed libraries so tools don't need to import
        # (they still can, these are just convenience pre-loads)
        _preload = ["requests", "json", "base64", "re", "datetime", "time"]
        for mod_name in _preload:
            try:
                import importlib
                namespace[mod_name] = importlib.import_module(mod_name)
            except ImportError:
                pass

        try:
            from pydantic import BaseModel, Field
            from typing import Optional, List, Dict, Any, Union
            namespace.update({
                "BaseModel": BaseModel, "Field": Field,
                "Optional": Optional, "List": List,
                "Dict": Dict, "Any": Any, "Union": Union,
            })
        except ImportError:
            pass

        exec(code, namespace)

        # ── Step 4: Find tool class ───────────────────────────────────────
        tool_class = None

        if tool_class_name and tool_class_name in namespace:
            tool_class = namespace[tool_class_name]
            print(f"[ToolRunner] Found class: {tool_class_name}")
        else:
            # Auto-detect: first class in namespace with a run() method
            for name, obj in namespace.items():
                if (isinstance(obj, type)
                        and not name.startswith("_")
                        and name not in ("BaseModel", "Field")
                        and hasattr(obj, "run")
                        and callable(getattr(obj, "run", None))):
                    tool_class = obj
                    print(f"[ToolRunner] Auto-detected class: {name}")
                    break

        if not tool_class:
            return json.dumps({
                "error":   True,
                "message": (
                    f"Class '{tool_class_name}' not found in tool code. "
                    f"Make sure 'Tool Class' field matches the class name exactly."
                )
            })

        # ── Step 5: Instantiate ───────────────────────────────────────────
        try:
            tool_instance = tool_class()
        except Exception as e:
            return json.dumps({
                "error":   True,
                "message": f"Cannot instantiate {tool_class_name}: {str(e)}"
            })

        # ── Step 6: Match run() kwargs by exact name only ─────────────────
        # No aliases. No hardcoding. Pure name matching.
        # If the JSON has "repo" and run() has "repo" → matched.
        # If the JSON has "github_repo" and run() has "repo" → NOT matched here.
        # The tool's run() method handles that via os.environ.get("GITHUB_REPO").
        sig        = inspect.signature(tool_instance.run)
        param_list = list(sig.parameters.items())[1:]  # skip 'self'
        kwargs     = {}

        for param_name, param in param_list:
            if param_name in input_data and input_data[param_name]:
                kwargs[param_name] = input_data[param_name]
                print(f"[ToolRunner] Matched param: {param_name}")

        print(f"[ToolRunner] Calling {tool_class_name}.run() | matched params: {list(kwargs.keys())}")

        # ── Step 7: Call run() ────────────────────────────────────────────
        result = tool_instance.run(**kwargs)
        output = str(result)
        print(f"[ToolRunner] ✓ Completed — {len(output)} chars returned")
        return output

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[ToolRunner] ERROR:\n{tb}")
        return json.dumps({
            "error":   True,
            "message": f"{tool_class_name} failed: {str(e)}",
        })

    finally:
        # ── Step 8: Restore all env vars ─────────────────────────────────
        for env_key, old_val in old_env_values.items():
            if old_val is None:
                os.environ.pop(env_key, None)
            else:
                os.environ[env_key] = old_val