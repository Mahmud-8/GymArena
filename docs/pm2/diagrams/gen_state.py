"""State diagrams for the main objects of the three PM2 scenarios (lab 5 style)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umlsvg import (SVG, ACTION_RED, STATE_EDGE, final, initial, note, state_box,  # noqa: E402
                    title, transition)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "png")
os.makedirs(OUT, exist_ok=True)


def two_lines(svg, x, y, event, action, anchor="start"):
    svg.text(x, y, event, size=13, fill=STATE_EDGE, anchor=anchor)
    if action:
        svg.text(x, y + 17, "/ " + action, size=13, fill=ACTION_RED, anchor=anchor)


def membership():
    svg = SVG(1380, 440)
    title(svg, "Membership Management - State Diagram (main object: Membership)")
    y = 170
    ini = initial(svg, 50, y + 24)
    nos = state_box(svg, 110, y, "No Subscription", min_w=190)
    act = state_box(svg, 640, y, "Active", min_w=170)
    exp = state_box(svg, 1150, y, "Expired", min_w=170)
    transition(svg, [(ini[0] + 9, ini[1]), (nos.x, ini[1])])
    transition(svg, [nos.right(), act.left()])
    two_lines(svg, nos.x + nos.w + 12, y + 2, "recordSubscription(start, expiry)", None)
    svg.text(nos.x + nos.w + 12, y + 19, "[expiry >= today]", size=13, fill=STATE_EDGE)
    transition(svg, [act.right(), exp.left()])
    two_lines(svg, act.x + act.w + 14, y + 2, "checkExpiry(today) [expiry < today]", None)
    # self loop renew on Active
    x0, x1 = act.x + 40, act.x + act.w - 40
    transition(svg, [(x0, act.y), (x0, 85), (x1, 85), (x1, act.y)])
    two_lines(svg, act.cx, 53, "renew(revised) [revised > expiry]", "record = new RenewalRecord(...)",
              anchor="middle")
    # Expired -> Active below
    transition(svg, [exp.bottom(), (exp.cx, 330), (act.cx, 330), act.bottom()])
    two_lines(svg, (act.cx + exp.cx) / 2, 356, "renew(revised) [revised > expiry and revised >= today]",
              "record = new RenewalRecord(...)", anchor="middle")
    note(svg, 40, 300, ["Rejected events (IllegalStateException /",
                        "IllegalArgumentException), state unchanged:",
                        "- renew() in No Subscription",
                        "- recordSubscription() in Active or Expired",
                        "- renew() with revised <= current expiry"])
    return svg.save(os.path.join(OUT, "state_membership"))


def session():
    svg = SVG(1420, 760)
    title(svg, "Session Management - State Diagram (main object: ChallengeSession)")
    r1, r2, r3 = 170, 430, 640
    ini = initial(svg, 45, r1 + 24)
    cre = state_box(svg, 95, r1, "Created", min_w=150)
    act = state_box(svg, 520, r1, "Active", min_w=180)
    com = state_box(svg, 1110, r1, "Completed", min_w=170)
    pau = state_box(svg, 520, r2, "Paused", min_w=180)
    sto = state_box(svg, 1110, r2, "Stopped", min_w=170)
    inc = state_box(svg, 520, r3, "Incomplete", min_w=180)
    transition(svg, [(ini[0] + 9, ini[1]), (cre.x, ini[1])])
    svg.text(cre.cx, cre.y - 12, "new(mode, rules, participants)", size=12, fill=STATE_EDGE, anchor="middle")
    svg.text(cre.cx, cre.y + cre.h + 18, "[1 member SOLO / 2 distinct 1v1]", size=12, fill=STATE_EDGE,
             anchor="middle")
    transition(svg, [cre.right(), act.left()])
    two_lines(svg, cre.x + cre.w + 12, r1 + 2, "start() [allPositionsReliable]", "activeSince = now")
    transition(svg, [act.right(), com.left()])
    two_lines(svg, act.x + act.w + 12, r1 - 14, "complete() [allTargetsReached or", None)
    svg.text(act.x + act.w + 12, r1 + 3, "activeTime >= timeLimit]", size=13, fill=STATE_EDGE)
    svg.text(act.x + act.w + 12, r1 + 20, "/ stop timer", size=13, fill=ACTION_RED)
    # self loop
    x0, x1 = act.x + 45, act.x + act.w - 45
    transition(svg, [(x0, act.y), (x0, 95), (x1, 95), (x1, act.y)])
    two_lines(svg, act.cx, 63, "addRepetition(memberId)", "participant.addRepetition()", anchor="middle")
    # Active <-> Paused
    xa, xb = act.x + 50, act.x + 120
    transition(svg, [(xa, act.y + act.h), (xa, pau.y)])
    two_lines(svg, xa - 10, 300, "trackingLost(position)", "stop timer; record interruption", anchor="end")
    transition(svg, [(xb, pau.y), (xb, act.y + act.h)])
    two_lines(svg, xb + 10, 300, "resume() [trackingReliable and", None)
    svg.text(xb + 10, 317, "assignmentsConfirmed]", size=13, fill=STATE_EDGE)
    svg.text(xb + 10, 334, "/ activeSince = now", size=13, fill=ACTION_RED)
    # Active -> Stopped
    xs = act.x + act.w - 20
    transition(svg, [(xs, act.y + act.h), (xs, 262), (sto.cx, 262), sto.top()])
    two_lines(svg, 905, 236, "reportDiscomfort()", "stop timer; record DISCOMFORT")
    # Paused -> Stopped
    transition(svg, [pau.right(), sto.left()])
    svg.rich(pau.x + pau.w + 14, r2 + 4, [("reportDiscomfort() ", STATE_EDGE, False),
                                          ("/ record DISCOMFORT", ACTION_RED, False)])
    # Paused -> Incomplete
    transition(svg, [pau.bottom(), inc.top()])
    two_lines(svg, pau.cx + 10, 555, "closeIncomplete() [tracking or identity unresolved]", None)
    # finals
    f1 = final(svg, 1350, r1 + 24)
    transition(svg, [com.right(), (f1[0] - 12, f1[1])])
    f2 = final(svg, 1350, r2 + 24)
    transition(svg, [sto.right(), (f2[0] - 12, f2[1])])
    f3 = final(svg, 820, r3 + 24)
    transition(svg, [inc.right(), (f3[0] - 12, f3[1])])
    note(svg, 40, 560, ["Rejected (IllegalStateException), state unchanged:",
                        "- start() without reliable tracking",
                        "- resume() unless reliable and confirmed",
                        "- addRepetition() / complete() while Paused",
                        "- any event in a final state"])
    return svg.save(os.path.join(OUT, "state_session"))


def member():
    svg = SVG(1330, 410)
    title(svg, "Member Management - State Diagram (main object: WeightReading)")
    y = 100
    ini = initial(svg, 50, y + 24)
    pen = state_box(svg, 440, y, "Pending Confirmation", min_w=240)
    con = state_box(svg, 1010, y, "Confirmed", min_w=170)
    dis = state_box(svg, 470, 300, "Discarded", min_w=180)
    transition(svg, [(ini[0] + 9, ini[1]), pen.left()])
    two_lines(svg, 72, y + 2, "capture(raw) [raw.stable and", None)
    svg.text(72, y + 19, "20 <= raw.weightKg <= 300]", size=13, fill=STATE_EDGE)
    transition(svg, [pen.right(), con.left()])
    two_lines(svg, pen.x + pen.w + 14, y + 2, "confirm(memberId) [memberId = owner]", "confirmedAt = now")
    transition(svg, [pen.bottom(), (pen.cx, dis.y)])
    svg.text(pen.cx + 10, 230, "reject()", size=13, fill=STATE_EDGE)
    f1 = final(svg, 1260, y + 24)
    transition(svg, [con.right(), (f1[0] - 12, f1[1])])
    f2 = final(svg, 760, 324)
    transition(svg, [dis.right(), (f2[0] - 12, f2[1])])
    note(svg, 40, 240, ["Invalid reading (unstable, < 20 kg or > 300 kg):",
                        "InvalidScaleReadingException, no object is",
                        "created and the last accepted weight is kept",
                        "(FR-10.4).",
                        "Rejected: confirm() by another member,",
                        "confirm()/reject() in Confirmed or Discarded."])
    return svg.save(os.path.join(OUT, "state_weight_reading"))


def challenge():
    svg = SVG(1380, 470)
    title(svg, "Challenge Management - State Diagram (main object: ChallengeRuleVersion)")
    y = 110
    ini = initial(svg, 50, y + 24)
    dr = state_box(svg, 380, y, "Draft", min_w=170)
    ap = state_box(svg, 900, y, "Approved", min_w=170, activities=["do / shown before attempts (summary)"])
    rj = state_box(svg, 380, 320, "Rejected", min_w=170)
    sp = state_box(svg, 900, 320, "Superseded", min_w=170)
    transition(svg, [(ini[0] + 9, ini[1]), (dr.x, ini[1])])
    svg.text(72, y + 2, "create(exercise, level, version, target,", size=13, fill=STATE_EDGE)
    svg.text(72, y + 19, "time, points, deduction, winnerRule)", size=13, fill=STATE_EDGE)
    svg.text(72, y + 60, "[target > 0, time > 0, points >= 0]", size=13, fill=STATE_EDGE)
    transition(svg, [dr.right(0.5), (ap.x, dr.cy)])
    two_lines(svg, dr.x + dr.w + 14, y + 2, "approve(trainerId) [trainerId given]", "approvedBy = trainerId; approvedAt = now")
    transition(svg, [dr.bottom(), rj.top()])
    two_lines(svg, dr.cx + 10, 250, "reject(trainerId, reason) [reason given]", "rejectionReason = reason")
    transition(svg, [(sp.cx, ap.y + ap.h), sp.top()])
    two_lines(svg, sp.cx + 10, 255, "supersede() [newer version approved]", "supersededAt = now")
    f1 = final(svg, 690, 344)
    transition(svg, [rj.right(), (f1[0] - 12, f1[1])])
    f2 = final(svg, 1250, 344)
    transition(svg, [sp.right(), (f2[0] - 12, f2[1])])
    note(svg, 40, 280, ["Rejected (IllegalStateException), state unchanged:",
                        "- approve() / reject() unless Draft",
                        "- supersede() unless Approved",
                        "- summary() unless Approved"])
    return svg.save(os.path.join(OUT, "state_challenge_rule"))


if __name__ == "__main__":
    for fn in (membership, session, member, challenge):
        print(fn())
