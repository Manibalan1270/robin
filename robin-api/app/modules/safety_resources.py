"""India mental-health helplines shown when a crisis is detected.

Verified November 2026. Numbers change - re-check them before any public launch.
(The earlier list included KIRAN 1800-599-0019, which is no longer the national
line, and old iCALL/Vandrevala numbers; those were removed.)
"""

INDIA_HELPLINES = {
    "TELE_MANAS": {
        "name": "Tele-MANAS (Govt. of India)",
        "number": "14416 or 1-800-891-4416",
        "hours": "24x7, free, many Indian languages",
    },
    "ICALL": {
        "name": "iCALL (TISS)",
        "number": "9152987821",
        "hours": "Mon-Sat, 10 AM - 8 PM",
    },
    "EMERGENCY": {
        "name": "Emergency services",
        "number": "112",
        "hours": "24x7 - if you are in immediate danger",
    },
}

CRISIS_RESPONSE_TEMPLATE = """I'm really glad you told me. It sounds like you're going through something very painful, and your safety matters most right now.

You don't have to handle this alone. Please reach out to someone who can talk with you right now:

{resources_list}

If you can, also tell someone you trust nearby how you're feeling. I'm still here to talk with you.
"""
