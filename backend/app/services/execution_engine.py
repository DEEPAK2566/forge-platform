"""
Execution Engine — runs workflow graphs.

Flow:
1. Load workflow nodes + edges
2. Topological sort
3. Execute nodes in order
4. For each node: run tools first with REAL execution,
   then pass real tool output to the LLM
5. Pass each node's LLM output to its children as input
"""

import traceback
import json as _json
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.models.execution import Execution, ExecutionLog
from app.models.agent import Agent
from app.models.workflow import Workflow
from app.services.llm_service import call_llm


# ── Helpers ───────────────────────────────────────────────────────────────────

def _mark_execution_failed(execution_id: int, error: str, db):
    exec_rec = db.query(Execution).filter(Execution.id == execution_id).first()
    if exec_rec:
        exec_rec.status      = "failed"
        exec_rec.error       = error
        exec_rec.finished_at = datetime.now(timezone.utc)
        db.commit()
    print(f"[Engine] Execution {execution_id} FAILED: {error}")


def _topological_sort(nodes: list, edges: list) -> list:
    if not nodes:
        return []
    in_degree = {n["id"]: 0 for n in nodes}
    outgoing  = {n["id"]: [] for n in nodes}
    for edge in edges:
        src = edge.get("source", "")
        tgt = edge.get("target", "")
        if src in in_degree and tgt in in_degree:
            in_degree[tgt] += 1
            outgoing[src].append(tgt)
    queue  = [nid for nid, deg in in_degree.items() if deg == 0]
    result = []
    while queue:
        current = queue.pop(0)
        result.append(current)
        for child in outgoing[current]:
            in_degree[child] -= 1
            if in_degree[child] == 0:
                queue.append(child)
    return result


def _get_incoming(node_id: str, edges: list) -> list:
    return [e["source"] for e in edges if e.get("target") == node_id]


def _build_tool_input(original_input: str, current_input: str) -> str:
    """
    Merge the original workflow input (credentials/variables) with the
    current agent input (data produced by previous agents) into one JSON.

    The merged JSON is what gets passed to each tool so it has access to
    both the user-supplied credentials AND the data it needs to process.

    Keys in the merged dict:
      - Everything from original_input JSON (github_token, jira_base_url, etc.)
      - 'content' = current_input  (data to write, process, or analyze)
      - 'query'   = current_input  (alias for reader tools)

    The tool_runner sets ALL these as env vars (uppercased) before calling run().
    The tool's run() method then reads them via os.environ.get().
    """
    merged = {}

    # Load credentials and variables from original workflow input
    if original_input:
        try:
            parsed = _json.loads(original_input.strip())
            if isinstance(parsed, dict):
                merged = {k: str(v).strip() for k, v in parsed.items() if v is not None}
        except Exception:
            pass

    # Inject current agent input as content and query
    if current_input and current_input.strip():
        merged["content"] = current_input.strip()
        if "query" not in merged:
            merged["query"] = current_input.strip()

    return _json.dumps(merged)


# ── Single node executor ──────────────────────────────────────────────────────

def _run_single_node(
    node:           dict,
    input_text:     str,
    execution_id:   int,
    position:       int,
    original_input: str = "",
) -> dict:

    node_id     = node["id"]
    agent_id    = node["data"].get("agent_id")
    agent_name  = node["data"].get("agent_name", "Unknown")
    agent_emoji = node["data"].get("avatar_emoji", "🤖")
    exec_type   = node["data"].get("execution_type", "sequential")

    db = SessionLocal()

    log = ExecutionLog(
        execution_id   = execution_id,
        node_id        = node_id,
        agent_id       = agent_id,
        agent_name     = agent_name,
        agent_emoji    = agent_emoji,
        execution_type = exec_type,
        status         = "running",
        input          = input_text[:3000],
        started_at     = datetime.now(timezone.utc),
    )
    db.add(log)
    db.commit()
    db.refresh(log)

    print(f"\n[Engine] ── Running: {agent_name} | exec_type: {exec_type}")

    try:
        from app.models.tools import Tool
        from app.services.tool_runner import run_tool

        agent = db.query(Agent).filter(Agent.id == agent_id).first()
        if not agent:
            raise ValueError(f"Agent ID {agent_id} not found")

        # ── Execute attached tools ────────────────────────────────────────
        tool_outputs = []
        tool_ids     = agent.tool_ids or []

        if tool_ids:
            print(f"[Engine] Tools attached: {tool_ids}")
            for tool_id in tool_ids:
                tool_record = db.query(Tool).filter(Tool.id == tool_id).first()
                if not tool_record:
                    print(f"[Engine] Tool ID {tool_id} not found — skipping")
                    continue

                # Merge: credentials from original_input + content from current input
                tool_input = _build_tool_input(original_input, input_text)

                tool_output = run_tool(tool_record, tool_input)
                tool_outputs.append({
                    "name":   tool_record.name,
                    "output": tool_output,
                })
                print(f"[Engine] Tool '{tool_record.name}': {len(tool_output)} chars")

        # ── Build enriched LLM prompt ─────────────────────────────────────
        if tool_outputs:
            tool_section = "\n\n".join(
                f"=== REAL OUTPUT FROM TOOL: {t['name']} ===\n{t['output']}"
                for t in tool_outputs
            )
            enriched_input = (
                f"{tool_section}\n\n"
                f"=== YOUR TASK ===\n"
                f"Use the REAL tool output above. Do NOT hallucinate or simulate.\n\n"
                f"Original context:\n{input_text}"
            )
        else:
            enriched_input = input_text

        # ── Call LLM ─────────────────────────────────────────────────────
        output = call_llm(agent, enriched_input)

        log.status      = "completed"
        log.output      = output[:5000]
        log.finished_at = datetime.now(timezone.utc)
        db.commit()

        print(f"[Engine] ✓ {agent_name} completed ({len(output)} chars)")
        return {"node_id": node_id, "output": output, "success": True}

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[Engine] ✗ {agent_name} failed:\n{tb}")
        log.status      = "failed"
        log.error       = str(e)
        log.finished_at = datetime.now(timezone.utc)
        db.commit()
        return {"node_id": node_id, "output": "", "success": False, "error": str(e)}

    finally:
        db.close()


# ── Main workflow runner ──────────────────────────────────────────────────────

def run_workflow(execution_id: int, workflow_id: int, user_input: str):
    db = SessionLocal()
    try:
        print(f"\n[Engine] ═══ Execution {execution_id} starting ═══")

        exec_rec = db.query(Execution).filter(Execution.id == execution_id).first()
        if not exec_rec:
            return

        exec_rec.status = "running"
        db.commit()

        workflow = db.query(Workflow).filter(Workflow.id == workflow_id).first()
        if not workflow:
            _mark_execution_failed(execution_id, "Workflow not found", db)
            return

        nodes = workflow.nodes or []
        edges = workflow.edges or []

        if not nodes:
            _mark_execution_failed(execution_id, "Workflow has no agents", db)
            return

        print(f"[Engine] '{workflow.name}' | {len(nodes)} nodes | {len(edges)} edges")

        sorted_node_ids = _topological_sort(nodes, edges)
        if not sorted_node_ids:
            _mark_execution_failed(execution_id, "Cannot determine order — possible cycle", db)
            return

        print(f"[Engine] Order: {sorted_node_ids}")

        node_map     = {n["id"]: n for n in nodes}
        node_outputs = {}
        position     = 0

        for node_id in sorted_node_ids:
            node       = node_map[node_id]
            exec_type  = node["data"].get("execution_type", "sequential")
            parent_ids = _get_incoming(node_id, edges)

            if not parent_ids:
                input_text = user_input or "Begin."
            elif exec_type == "merge":
                parts = []
                for pid in parent_ids:
                    if pid in node_outputs:
                        pname = node_map[pid]["data"].get("agent_name", pid)
                        parts.append(f"Result from {pname}:\n{node_outputs[pid]}")
                input_text = "\n\n---\n\n".join(parts) if parts else user_input
            else:
                input_text = user_input
                for pid in reversed(parent_ids):
                    if pid in node_outputs:
                        input_text = node_outputs[pid]
                        break

            db.close()

            result = _run_single_node(
                node,
                input_text,
                execution_id,
                position,
                original_input = user_input or "",
            )

            db = SessionLocal()
            position += 1

            if not result["success"]:
                _mark_execution_failed(
                    execution_id,
                    f"Agent '{node['data'].get('agent_name', node_id)}' failed: "
                    f"{result.get('error', 'Unknown')}",
                    db
                )
                return

            node_outputs[node_id] = result["output"]

        exec_rec = db.query(Execution).filter(Execution.id == execution_id).first()
        if exec_rec:
            exec_rec.status      = "completed"
            exec_rec.finished_at = datetime.now(timezone.utc)
            db.commit()

        print(f"[Engine] ═══ Execution {execution_id} COMPLETED ═══\n")

    except Exception as e:
        tb = traceback.format_exc()
        print(f"[Engine] UNEXPECTED ERROR:\n{tb}")
        try:
            _mark_execution_failed(execution_id, f"Unexpected: {str(e)}", db)
        except Exception:
            pass
    finally:
        try:
            db.close()
        except Exception:
            pass