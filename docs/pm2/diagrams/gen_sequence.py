"""Sequence diagrams for the three PM2 scenarios.

Lifelines are the actors (stick figures) and the GymArena subsystems
(rectangles). Messages inside one subsystem are self-messages; their numbers
match the collaboration diagrams and the // 1.x comments in domain-java.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umlsvg import sequence  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "png")
os.makedirs(OUT, exist_ok=True)


def C(f, t, text):
    return {"f": f, "t": t, "text": text, "kind": "call"}


def R(f, t, text, pop=True):
    return {"f": f, "t": t, "text": text, "kind": "ret", "pop": pop}


def V(f, t, text):
    return {"f": f, "t": t, "text": text, "kind": "void"}


def S(p, text):
    return {"f": p, "t": p, "text": text, "kind": "self"}


def membership():
    parts = [("staff", "Staff", "actor"),
             ("mm", "Membership Management", "participant"),
             ("mem", "Member Management", "participant"),
             ("nm", "Notification Management", "participant")]
    msgs = [C("staff", "mm", '1: renew("MBR-0042", 2027-02-28, "STF-07")'),
            C("mm", "mem", '1.1: exists("MBR-0042")'),
            R("mem", "mm", "true"),
            R("mm", "staff", "MemberNotFoundException", pop=False),
            S("mm", '1.2: m42 := findByMemberId("MBR-0042")'),
            S("mm", '1.3: r1 := m42.renew(2027-02-28, "STF-07", now, today)'),
            S("mm", "1.4: saveRenewal(m42, r1)"),
            V("mm", "nm", "1.5: publish(RenewalChanged(MBR-0042, 2026-11-30, 2027-02-28))"),
            R("mm", "staff", "r1 (expiry 2027-02-28, ACTIVE)")]
    frames = [{"kind": "alt", "guard": "[found = false]", "start": 3, "end": 7, "else_at": 4,
               "else_guard": "[found = true]", "parts": ("staff", "nm")}]
    return sequence(os.path.join(OUT, "seq_membership_renewal"),
                    "Membership Management - Record a Membership Renewal (Sequence Diagram)", parts, msgs, frames)


def session():
    parts = [("trainer", "Trainer", "actor"),
             ("sm", "Session Management", "participant"),
             ("etm", "Exercise Tracking Management", "participant")]
    msgs = [C("etm", "sm", '1: onTrackingLost("SES-1001", "RIGHT")'),
            S("sm", '1.1: s1001 := findById("SES-1001")'),
            S("sm", "1.2: true := shouldPause(s1001)"),
            S("sm", '1.3: s1001.pause(TRACKING_LOST, "RIGHT", 10:01:35)'),
            V("sm", "etm", '1.4: pauseCounting("SES-1001")'),
            S("sm", "1.5: save(s1001)"),
            R("sm", "etm", "PAUSED"),
            C("trainer", "sm", '2: confirmAssignments("SES-1001")'),
            S("sm", '2.1: s1001 := findById("SES-1001")'),
            C("sm", "etm", '2.2: isTrackingReliable("SES-1001")'),
            R("etm", "sm", "true"),
            S("sm", "2.3: true := canResume(s1001, true, true)"),
            S("sm", "2.4: s1001.resume(true, true, 10:02:05)"),
            V("sm", "etm", '2.5: resumeCounting("SES-1001")'),
            S("sm", "2.6: save(s1001)"),
            R("sm", "trainer", "ACTIVE")]
    frames = [{"kind": "opt", "guard": "[shouldPause = true]", "start": 3, "end": 5, "parts": ("sm", "etm")},
              {"kind": "opt", "guard": "[canResume = true]", "start": 12, "end": 14, "parts": ("sm", "etm")}]
    return sequence(os.path.join(OUT, "seq_session_recovery"),
                    "Session Management - Pause and Resume a Local 1v1 Attempt (Sequence Diagram)",
                    parts, msgs, frames)


def member():
    parts = [("member", "Member (kiosk)", "actor"),
             ("mgm", "Member Management", "participant"),
             ("scale", "Electronic Scale", "actor")]
    msgs = [C("member", "mgm", '1: captureReading("MBR-0042")'),
            S("mgm", '1.1: omar := findById("MBR-0042")'),
            C("mgm", "scale", "1.2: readStableWeight()"),
            R("scale", "mgm", "raw (78.4 kg, stable = true)"),
            R("mgm", "member", "InvalidScaleReadingException", pop=False),
            S("mgm", '1.3: "WR-0310" := nextReadingId()'),
            S("mgm", '1.4: «create» wr310 := WeightReading.capture("WR-0310", omar, raw)'),
            S("mgm", "1.5: save(wr310)"),
            R("mgm", "member", "wr310 (78.4 kg, PENDING_CONFIRMATION)"),
            C("member", "mgm", '2: confirmReading("WR-0310", "MBR-0042")'),
            S("mgm", '2.1: wr310 := findById("WR-0310")'),
            S("mgm", '2.2: wr310.confirm("MBR-0042", 09:40:30)'),
            S("mgm", "2.3: save(wr310)"),
            R("mgm", "member", "wr310 (CONFIRMED)")]
    frames = [{"kind": "alt", "guard": "[raw invalid]", "start": 4, "end": 7, "else_at": 5,
               "else_guard": "[raw valid]", "parts": ("member", "scale")}]
    return sequence(os.path.join(OUT, "seq_member_weight"),
                    "Member Management - Capture and Confirm a Scale Reading (Sequence Diagram)",
                    parts, msgs, frames)


def challenge():
    parts = [("trainer", "Trainer", "actor"),
             ("member", "Member (kiosk)", "actor"),
             ("cm", "Challenge Management", "participant"),
             ("mgm", "Member Management", "participant")]
    msgs = [C("trainer", "cm", '1: approveRules("CR-SQUAT-2-v4", "TRN-03")'),
            S("cm", '1.1: v4 := findRuleVersion("CR-SQUAT-2-v4")'),
            S("cm", '1.2: v3 := findApprovedRule("SQUAT", 2)'),
            S("cm", '1.3: v4.approve("TRN-03", now)'),
            S("cm", "1.4: v3.supersede(now)"),
            S("cm", "1.5: saveApproval(v4, v3)"),
            R("cm", "trainer", "v4 (APPROVED, version 4)"),
            C("member", "cm", '2: presentRules("MBR-0042", "SQUAT")'),
            C("cm", "mgm", '2.1: exists("MBR-0042")'),
            R("mgm", "cm", "true"),
            S("cm", '2.2: 2 := findCurrentLevel("MBR-0042", "SQUAT")'),
            S("cm", '2.3: v4 := findApprovedRule("SQUAT", 2)'),
            S("cm", "2.4: summary := v4.summary()"),
            R("cm", "member", "target 22, 120 s, +12 / -3, MOST_REPETITIONS")]
    frames = [{"kind": "opt", "guard": "[an approved version exists]", "start": 4, "end": 4, "parts": ("cm", "mgm")}]
    return sequence(os.path.join(OUT, "seq_challenge_rules"),
                    "Challenge Management - Approve and Present Versioned Challenge Rules (Sequence Diagram)",
                    parts, msgs, frames)


if __name__ == "__main__":
    for fn in (membership, session, member, challenge):
        print(fn())
