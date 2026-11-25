"""Object diagrams and the collaboration diagrams drawn on top of them.

Each scenario defines one layout (object centres and links). The object diagram
shows the snapshot with sample values; the collaboration diagram reuses the
same objects and links and adds the numbered messages. Every link corresponds
to an association or dependency in the class diagram of that service.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umlsvg import (SVG, Box, actor_icon, comm_link, link, object_at, title, tw)  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "png")
os.makedirs(OUT, exist_ok=True)


def render(scn):
    # ---- object diagram (no actors, shifted up) ----
    shift = scn["obj_shift"]
    svg = SVG(scn["width"], scn["height"] - shift)
    title(svg, scn["title"] + " (Object Diagram)")
    boxes = {}
    for oid, (cx, cy, name, attrs) in scn["objects"].items():
        boxes[oid] = object_at(svg, cx, cy - shift, name, attrs)
    for a, b, name, m1, m2, *rest in scn["links"]:
        off = rest[0] if rest else (6, -6)
        link(svg, boxes[a], boxes[b], name, m1, m2, name_off=off)
    # redraw boxes over link ends
    for oid, (cx, cy, name, attrs) in scn["objects"].items():
        object_at(svg, cx, cy - shift, name, attrs)
    obj_png = svg.save(os.path.join(OUT, "obj_" + scn["key"]))

    # ---- collaboration diagram ----
    svg = SVG(scn["width"], scn["height"])
    title(svg, scn["title"] + " (Collaboration Diagram)")
    boxes = {}
    for oid, (cx, cy, name, attrs) in scn["objects"].items():
        boxes[oid] = object_at(svg, cx, cy, name, ())
    for aid, (cx, top, label) in scn["actors"].items():
        boxes[aid] = Box(cx - 0.5, top + 71.5, 1, 1)
    sub_boxes = {}
    for sid, (cx, cy, label) in scn.get("subsystems", {}).items():
        w = tw(label, 13) + 24
        boxes[sid] = sub_boxes[sid] = Box(cx - w / 2, cy - 15, w, 30)
    msgs = scn["messages"]
    pairs = [(a, b) for a, b, *_ in scn["links"]] + [k for k in msgs if k not in
                                                      [(a, b) for a, b, *_ in scn["links"]]]
    for a, b in pairs:
        comm_link(svg, boxes[a], boxes[b], [])
    for a, b in pairs:
        spec = msgs.get((a, b))
        if spec:
            comm_link(svg, boxes[a], boxes[b], spec["m"], side=spec.get("side", 1),
                      shift=spec.get("shift", 0.0), dx=spec.get("dx", 0), dy=spec.get("dy", 0), draw_line=False)
    for oid, (cx, cy, name, attrs) in scn["objects"].items():
        object_at(svg, cx, cy, name, ())
    for aid, (cx, top, label) in scn["actors"].items():
        svg.rect(cx - 40, top - 2, 80, 70, fill="#FFFFFF", stroke="#FFFFFF", sw=0)
        actor_icon(svg, cx, top, label)
    for sid, b in sub_boxes.items():
        svg.rect(b.x, b.y, b.w, b.h, fill="#E6E6E6", rx=2)
        svg.text(b.cx, b.cy + 4.5, scn["subsystems"][sid][2], size=13, anchor="middle")
    col_png = svg.save(os.path.join(OUT, "collab_" + scn["key"]))
    return obj_png, col_png


MEMBERSHIP = {
    "key": "membership_renewal",
    "title": "Membership Management - Record a Membership Renewal",
    "width": 1300, "height": 770, "obj_shift": 120,
    "actors": {"staff": (650, 40, "Staff (STF-07)")},
    "objects": {
        "proc": (650, 205, "processor : RenewalProcessor", ["clock = 2026-11-22T10:15Z"]),
        "client": (190, 205, "profileClient : MemberProfileClient", ['baseUrl = "http://member-service:8000"']),
        "outbox": (1110, 205, "outbox : RenewalOutbox", ['table = "renewal_outbox"']),
        "store": (650, 440, "store : SqlMembershipStore", ['database = "gymarena_membership"']),
        "m42": (1110, 440, "m42 : Membership",
                ['memberId = "MBR-0042"', 'whatsappNumber = "+201000000042"', "startDate = 2026-08-01",
                 "expiryDate = 2027-02-28", "status = ACTIVE"]),
        "r1": (1110, 665, "r1 : RenewalRecord",
               ['memberId = "MBR-0042"', "previousExpiry = 2026-11-30", "revisedExpiry = 2027-02-28",
                'recordedBy = "STF-07"', "recordedAt = 2026-11-22T10:15Z"]),
    },
    "links": [
        ("proc", "client", "memberLookup", "1", "1"),
        ("proc", "outbox", "renewalFeed", "1", "1"),
        ("proc", "store", "store", "1", "1"),
        ("proc", "m42", "renews", "1", "1", (10, -10)),
        ("store", "m42", "holds", "1", "0..*"),
        ("m42", "r1", "creates", "1", "0..*"),
    ],
    "messages": {
        ("staff", "proc"): {"m": [("1: r1 := renew(memberId, revisedExpiry, staffId)", True)], "side": 1},
        ("proc", "client"): {"m": [("1.1: found := exists(memberId)", True)], "side": -1},
        ("proc", "outbox"): {"m": [("1.5: publish(RenewalChanged.from(r1))", True)], "side": -1},
        ("proc", "store"): {"m": [("1.2: m42 := findByMemberId(memberId)", True),
                                  ("1.4: saveRenewal(m42, r1)", True)], "side": -1},
        ("proc", "m42"): {"m": [("1.3: r1 := renew(revisedExpiry, staffId, now, today)", True)], "side": -1,
                          "dx": 30},
        ("m42", "r1"): {"m": [("1.3.1: «create»", True)], "side": 1},
    },
}

SESSION = {
    "key": "session_recovery",
    "title": "Session Management - Pause and Resume a Local 1v1 Attempt",
    "width": 1300, "height": 790, "obj_shift": 110,
    "actors": {"trainer": (920, 40, "Trainer")},
    "subsystems": {"tracker": (330, 75, "Exercise Tracking Management")},
    "objects": {
        "lc": (650, 210, "lifecycle : SessionLifecycle", []),
        "store": (180, 210, "store : SqlSessionStore", ['database = "gymarena_session"']),
        "policy": (1110, 210, "policy : RecoveryPolicy", []),
        "s": (650, 445, "s1001 : ChallengeSession",
              ['sessionId = "SES-1001"', "mode = LOCAL_1V1", "status = PAUSED", "accumulatedActive = 95 s",
               "activeSince = null"]),
        "tc": (1110, 445, "trackingClient : TrackingClient", ['baseUrl = "http://exercise-tracking-service:8000"']),
        "p1": (190, 700, "p1 : SessionParticipant",
               ['memberId = "MBR-0042"', 'position = "LEFT"', "acceptedRepetitions = 14"]),
        "p2": (500, 700, "p2 : SessionParticipant",
               ['memberId = "MBR-0057"', 'position = "RIGHT"', "acceptedRepetitions = 12"]),
        "rules": (800, 700, "rules : RuleSnapshot",
                  ['exercise = "SQUAT"', "level = 2", "targetRepetitions = 20", "timeLimit = 120 s",
                   "ruleVersion = 3", "ranked = true"]),
        "i1": (1110, 700, "i1 : SessionInterruption",
               ["reason = TRACKING_LOST", 'position = "RIGHT"', "at = 2026-11-22T10:01:35Z"]),
    },
    "links": [
        ("lc", "store", "store", "1", "1"),
        ("lc", "policy", "recoveryPolicy", "1", "1"),
        ("lc", "s", "manages", "1", "0..*"),
        ("lc", "tc", "tracking", "1", "1", (16, -4)),
        ("store", "s", "holds", "1", "0..*", (-30, -8)),
        ("s", "p1", "participants", "1", "1..2", (-60, 0)),
        ("s", "p2", "", "1", "", (0, 0)),
        ("s", "rules", "rules", "1", "1", (8, 0)),
        ("s", "i1", "interruptions", "1", "0..*", (10, 0)),
    ],
    "messages": {
        ("tracker", "lc"): {"m": [('1: onTrackingLost("SES-1001", "RIGHT")', True)], "side": -1, "dx": -60},
        ("trainer", "lc"): {"m": [('2: confirmAssignments("SES-1001")', True)], "side": -1, "dx": 50},
        ("lc", "store"): {"m": [("1.1: s1001 := findById(sessionId)", True), ("1.5: save(s1001)", True),
                                ("2.1: s1001 := findById(sessionId)", True), ("2.6: save(s1001)", True)],
                          "side": 1},
        ("lc", "policy"): {"m": [("1.2: true := shouldPause(s1001)", True),
                                 ("2.3: true := canResume(s1001, true, true)", True)], "side": 1},
        ("lc", "s"): {"m": [("1.3: pause(TRACKING_LOST, position, now)", True),
                            ("2.4: resume(true, true, now)", True)], "side": -1},
        ("lc", "tc"): {"m": [("1.4: pauseCounting(sessionId)", True),
                             ("2.2: true := isTrackingReliable(sessionId)", True),
                             ("2.5: resumeCounting(sessionId)", True)], "side": 1, "dx": 40, "dy": -20},
    },
}

MEMBER = {
    "key": "member_weight",
    "title": "Member Management - Capture and Confirm a Scale Reading",
    "width": 1300, "height": 640, "obj_shift": 110,
    "actors": {"member": (650, 40, "Member (kiosk)")},
    "objects": {
        "svc": (650, 210, "service : MeasurementService", []),
        "store": (190, 210, "store : SqlMemberStore", ['database = "gymarena_member"']),
        "scale": (1110, 210, "scale : SerialScaleAdapter", ['port = "COM3"']),
        "omar": (190, 500, "omar : MemberProfile",
                 ['memberId = "MBR-0042"', 'name = "Omar Adel"', "age = 24", 'memberCode = "GA-7Q4K"']),
        "wr": (650, 500, "wr310 : WeightReading",
               ['readingId = "WR-0310"', 'memberId = "MBR-0042"', "weightKg = 78.4",
                "readAt = 2026-11-22T09:40:12Z", "status = PENDING_CONFIRMATION", "confirmedAt = null"]),
        "raw": (1110, 500, "raw : ScaleReading", ["weightKg = 78.4", "stable = true", "readAt = 2026-11-22T09:40:12Z"]),
    },
    "links": [
        ("svc", "store", "memberStore, measurementStore", "1", "1", (-110, -8)),
        ("svc", "scale", "scale", "1", "1"),
        ("svc", "wr", "creates / confirms", "1", "0..*"),
        ("store", "omar", "holds", "1", "0..*"),
        ("store", "wr", "holds", "1", "0..*", (-30, -10)),
        ("wr", "omar", "measures", "0..*", "1", (-30, -8)),
        ("wr", "raw", "capturedFrom", "0..1", "1", (-40, -8)),
        ("scale", "raw", "supplies", "1", "0..*"),
    ],
    "messages": {
        ("member", "svc"): {"m": [('1: wr310 := captureReading("MBR-0042")', True),
                                  ('2: confirmReading("WR-0310", "MBR-0042")', True)], "side": 1},
        ("svc", "store"): {"m": [("1.1: omar := findById(memberId)", True),
                                 ('1.3: "WR-0310" := nextReadingId()', True),
                                 ("1.5: save(wr310)", True),
                                 ("2.1: wr310 := findById(readingId)", True),
                                 ("2.3: save(wr310)", True)], "side": 1},
        ("svc", "scale"): {"m": [("1.2: raw := readStableWeight()", True)], "side": 1},
        ("svc", "wr"): {"m": [("1.4: «create» capture(readingId, omar, raw)", True),
                              ("2.2: confirm(memberId, now)", True)], "side": 1},
    },
}


CHALLENGE = {
    "key": "challenge_rules",
    "title": "Challenge Management - Approve and Present Versioned Challenge Rules",
    "width": 1300, "height": 720, "obj_shift": 110,
    "actors": {"trainer": (430, 40, "Trainer (TRN-03)"), "member": (880, 40, "Member (kiosk)")},
    "objects": {
        "planner": (650, 205, "planner : ChallengePlanner", ["clock = 2026-11-22T11:00Z"]),
        "client": (190, 205, "profileClient : MemberProfileClient", ['baseUrl = "http://member-service:8000"']),
        "v4": (1110, 345, "v4 : ChallengeRuleVersion",
               ['ruleId = "CR-SQUAT-2-v4"', 'exercise = "SQUAT"', "level = 2", "version = 4",
                "targetRepetitions = 22", "timeAllowance = 120 s", "completionPoints = 12", "timeoutDeduction = 3",
                "status = APPROVED", 'approvedBy = "TRN-03"']),
        "v3": (190, 520, "v3 : ChallengeRuleVersion",
               ['ruleId = "CR-SQUAT-2-v3"', "version = 3", "targetRepetitions = 20", "completionPoints = 10",
                "timeoutDeduction = 3", "status = SUPERSEDED", "supersededAt = 2026-11-22T11:00Z"]),
        "store": (650, 620, "store : SqlChallengeStore", ['database = "gymarena_challenge"']),
    },
    "links": [
        ("planner", "client", "memberLookup", "1", "1"),
        ("planner", "v4", "approves", "1", "0..*", (6, -10)),
        ("planner", "v3", "supersedes", "1", "0..*", (-90, -6)),
        ("planner", "store", "store", "1", "1"),
        ("store", "v3", "holds", "1", "0..*", (-20, 16)),
        ("store", "v4", "holds", "1", "0..*", (10, 16)),
    ],
    "messages": {
        ("trainer", "planner"): {"m": [('1: v4 := approveRules("CR-SQUAT-2-v4", "TRN-03")', True)], "side": -1,
                                 "dx": -120},
        ("member", "planner"): {"m": [('2: summary := presentRules("MBR-0042", "SQUAT")', True)], "side": -1,
                                "dx": 110},
        ("planner", "client"): {"m": [("2.1: found := exists(memberId)", True)], "side": -1},
        ("planner", "store"): {"m": [("1.1: v4 := findRuleVersion(ruleId)", True),
                                     ('1.2: v3 := findApprovedRule("SQUAT", 2)', True),
                                     ("1.5: saveApproval(v4, v3)", True),
                                     ('2.2: 2 := findCurrentLevel(memberId, "SQUAT")', True),
                                     ('2.3: v4 := findApprovedRule("SQUAT", 2)', True)], "side": 1},
        ("planner", "v4"): {"m": [('1.3: approve("TRN-03", now)', True), ("2.4: summary()", True)], "side": -1,
                            "dx": 20},
        ("planner", "v3"): {"m": [("1.4: supersede(now)", True)], "side": -1, "dx": -20},
    },
}


if __name__ == "__main__":
    for scn in (MEMBERSHIP, SESSION, MEMBER, CHALLENGE):
        print(render(scn))
