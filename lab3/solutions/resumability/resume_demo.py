# resume_demo.py - shows RESUMABILITY step by step with plain HTTP (no MCP SDK).
#
#   1. initialize            -> server returns an Mcp-Session-Id
#   2. call "process-files"  -> the reply streams events, each with an "id:"
#   3. disconnect after the first progress event (simulates a network drop)
#   4. GET /mcp with "Last-Event-ID: <that id>" -> server replays the events
#      we missed, then the final result
#
# Run the server first (python server.py), then: python resume_demo.py
# Needs: pip install requests
import json
import requests

URL = "http://127.0.0.1:3000/mcp"
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/event-stream",
}


def read_events(response, stop_after=None):
    """Yield (event_id, data) for each SSE event; optionally stop early."""
    event_id, count = None, 0
    for raw in response.iter_lines(decode_unicode=True):
        if raw.startswith("id:"):
            event_id = raw[3:].strip()
        elif raw.startswith("data:"):
            data = raw[5:].strip()
            if not data:          # priming event: an id with no message
                continue
            yield event_id, json.loads(data)
            count += 1
            if stop_after and count >= stop_after:
                return


def describe(msg):
    if msg.get("method") == "notifications/message":
        return "progress: " + msg["params"]["data"]
    if "result" in msg:
        return "RESULT:   " + msg["result"]["content"][0]["text"]
    return json.dumps(msg)


# 1. initialize (an older protocol version, which uses session ids)
init = requests.post(URL, headers=HEADERS, json={
    "jsonrpc": "2.0", "id": 1, "method": "initialize",
    "params": {"protocolVersion": "2025-06-18", "capabilities": {},
               "clientInfo": {"name": "resume-demo", "version": "1.0"}},
})
session_id = init.headers["mcp-session-id"]
HEADERS["mcp-session-id"] = session_id
print("1. Session id:", session_id)

requests.post(URL, headers=HEADERS,
              json={"jsonrpc": "2.0", "method": "notifications/initialized"})

# 2. call the tool and read only the FIRST progress event
print("2. Calling process-files, reading one event, then disconnecting...")
call = requests.post(URL, headers=HEADERS, stream=True, json={
    "jsonrpc": "2.0", "id": 2, "method": "tools/call",
    "params": {"name": "process-files", "arguments": {}},
})
last_id = None
for event_id, msg in read_events(call, stop_after=1):
    last_id = event_id
    print(f"   id={event_id}  {describe(msg)}")

# 3. simulate a dropped connection
call.close()
print("3. Disconnected. Last-Event-ID =", last_id)

# 4. reconnect and resume from that event
print("4. Reconnecting with Last-Event-ID - replaying what we missed:")
resume = requests.get(URL, headers={**HEADERS, "Last-Event-ID": last_id}, stream=True)
for event_id, msg in read_events(resume):
    print(f"   id={event_id}  {describe(msg)}")
    if "result" in msg:
        break
resume.close()
print("Done - no events were lost.")
