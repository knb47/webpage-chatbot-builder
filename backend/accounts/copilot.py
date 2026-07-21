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


def chat(messages, current_yaml):
    """messages: [{role: user|assistant, content: str}]. Returns (reply, yaml|None)."""
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("ANTHROPIC_API_KEY is not set")

    # Latest user turn gets the current YAML appended as working context.
    payload_messages = [dict(m) for m in messages]
    if payload_messages and payload_messages[-1]["role"] == "user":
        payload_messages[-1]["content"] += (
            "\n\n[Current config the user sees in the editor:]\n```yaml\n"
            + (current_yaml or STARTER_YAML) + "\n```"
        )

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
    text = "".join(b.get("text", "") for b in resp.json().get("content", []))

    yaml_block = None
    fence = re.search(r"```(?:yaml|yml)\s*\n(.*?)```", text, re.DOTALL)
    if fence:
        yaml_block = fence.group(1).strip() + "\n"
        # The fence lives in the editor pane; keep chat text conversational.
        text = (text[: fence.start()] + text[fence.end():]).strip()
        if not text:
            text = "I've updated the config on the right — take a look."

    return text, yaml_block
