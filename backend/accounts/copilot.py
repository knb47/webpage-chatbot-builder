"""Config copilot — a Claude-backed assistant that helps users write chat-agent
configs conversationally.

The builder page shows this chat on the left and the working YAML on the
right. Each turn we send the conversation plus the current YAML; the model
answers conversationally and, whenever the config should change, returns the
complete updated YAML in a fenced block, which the UI swaps into the editor.

Called via plain `requests` (no SDK dependency); the key comes from
ANTHROPIC_API_KEY, same env the tenant Lambdas get.
"""

import os
import re

import requests
import yaml as pyyaml

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
MODEL = os.environ.get("CLAUDE_MODEL", "claude-haiku-4-5")

# A minimal valid config: the right pane starts from this.
STARTER_YAML = """\
bot_name: "My Assistant"
version: "1.0"

initialization:
  - role: "assistant"
  - context: >
      You are a friendly assistant. Describe here who the assistant is,
      what it knows, and how it should behave.
  - start_state: "start"

states:
  - state: "start"
    label: "Welcome"
    description: "Introduction and getting started"
    trigger: "When the user begins the conversation."
    goal: >
      Greet the user, explain what you can help with, and ask what they need.
    tools_available: []
    actions_available: []
    states_available: ["start"]
"""

SYSTEM_PROMPT = """\
You are the Config Copilot for Chapp, a platform that deploys chat agents
defined as YAML state machines. You help the user design their agent by
conversation, and you maintain their config for them.

The config format:
- top-level: bot_name, version, optional author
- initialization: list with `role` ("assistant"), `context` (the agent's
  persona/system prompt), and `start_state` (must match a state name)
- states: each has
    state (snake_case id), label (short UI title), description (one line),
    trigger (when the conversation should move INTO this state),
    goal (what the agent tries to accomplish while here),
    states_available (list of state ids reachable from here — include the
    state itself to allow staying),
    tools_available / actions_available (usually []),
    optional provide_user (list of {link, purpose}) for links to share.
- The last state in a flow is typically a summary/wrap-up state whose
  states_available is just itself (terminal).

Rules:
1. Interview the user about what they want (purpose, audience, stages,
   tone). Ask at most 1-2 focused questions per turn.
2. Whenever the config should change, output the COMPLETE updated YAML in a
   single ```yaml fenced block (never a fragment or diff), after your
   conversational reply. If nothing should change, output no fence.
3. Keep YAML valid: every states_available entry must be a defined state;
   start_state must exist; ids snake_case.
4. Aim for 3-6 states. Suggest a sensible flow early rather than
   interrogating endlessly — the user can always refine.
"""


def validate_config(yaml_text):
    """Structural validation of an engine config. Returns a list of problems
    (empty == valid)."""
    errors = []
    try:
        doc = pyyaml.safe_load(yaml_text)
    except pyyaml.YAMLError as e:
        return [f"Not parseable YAML: {e}"]
    if not isinstance(doc, dict):
        return ["Config must be a YAML mapping."]

    init = doc.get("initialization")
    start_state = None
    if not isinstance(init, list):
        errors.append("Missing 'initialization' list.")
    else:
        for item in init:
            if isinstance(item, dict) and "start_state" in item:
                start_state = item["start_state"]
        if not start_state:
            errors.append("initialization must define start_state.")

    states = doc.get("states")
    if not isinstance(states, list) or not states:
        errors.append("Missing non-empty 'states' list.")
        return errors

    ids = set()
    for s in states:
        if not isinstance(s, dict) or "state" not in s:
            errors.append("Every state needs a 'state' id.")
            continue
        ids.add(s["state"])
    if start_state and start_state not in ids:
        errors.append(f"start_state '{start_state}' is not a defined state.")
    for s in states:
        if not isinstance(s, dict):
            continue
        for field in ("trigger", "goal", "states_available"):
            if field not in s:
                errors.append(f"State '{s.get('state')}' is missing '{field}'.")
        for ref in s.get("states_available") or []:
            if ref not in ids:
                errors.append(
                    f"State '{s.get('state')}' references undefined state '{ref}'.")
    return errors


def _call_claude(payload_messages):
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")
    resp = requests.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json",
        },
        json={
            "model": MODEL,
            "max_tokens": 4096,
            "system": SYSTEM_PROMPT,
            "messages": payload_messages,
        },
        timeout=120,
    )
    resp.raise_for_status()
    return "".join(b.get("text", "") for b in resp.json().get("content", []))


def _extract_fence(text):
    fence = re.search(r"```(?:yaml|yml)\s*\n(.*?)```", text, re.DOTALL)
    if not fence:
        return text, None
    yaml_block = fence.group(1).strip() + "\n"
    # The fence lives in the editor pane; keep chat text conversational.
    text = (text[: fence.start()] + text[fence.end():]).strip()
    return text or "I've updated the config on the right — take a look.", yaml_block


def chat(messages, current_yaml, max_fix_rounds=2):
    """messages: [{role: user|assistant, content: str}]. Returns (reply, yaml|None).

    If the model returns a config that fails validation, the errors are sent
    back to it (up to max_fix_rounds) before anything reaches the user; an
    invalid config never replaces the editor contents.
    """
    payload_messages = [dict(m) for m in messages]
    if payload_messages and payload_messages[-1]["role"] == "user":
        payload_messages[-1]["content"] += (
            "\n\n[Current config the user sees in the editor:]\n```yaml\n"
            + (current_yaml or STARTER_YAML) + "\n```"
        )

    text = _call_claude(payload_messages)
    reply, yaml_block = _extract_fence(text)

    rounds = 0
    while yaml_block and validate_config(yaml_block) and rounds < max_fix_rounds:
        problems = validate_config(yaml_block)
        payload_messages.append({"role": "assistant", "content": text})
        payload_messages.append({"role": "user", "content": (
            "[Automated validator] The config you produced has problems:\n- "
            + "\n- ".join(problems)
            + "\nReturn the corrected COMPLETE config in a ```yaml fence."
        )})
        text = _call_claude(payload_messages)
        reply, yaml_block = _extract_fence(text)
        rounds += 1

    if yaml_block and validate_config(yaml_block):
        # Still broken after retries: keep the conversation, drop the config.
        reply += "\n\n(I drafted a config but it didn't pass validation, so I left your current one untouched — tell me to try again.)"
        yaml_block = None

    return reply, yaml_block
