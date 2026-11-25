"""Updated (PM2) class diagrams for the three scenario services.

Classes and signatures match domain-java/src/main/java/com/gymarena/*. Grey
«adapter» classes are realized in the Python service and replaced by Mockito
mocks in the unit tests.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from umlsvg import SVG, class_box, label_line, note, title  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "png")
os.makedirs(OUT, exist_ok=True)
ADAPTER = "#E4E4E4"


def assoc(svg, pts, name=None, m_end=None, name_at=None, m_at=None):
    """Directed association (open arrow at the target)."""
    svg.arrow(pts, head="open", size=10)
    if name:
        svg.text(name_at[0], name_at[1], name, size=11)
    if m_end:
        svg.text(m_at[0], m_at[1], m_end, size=11)


def dep(svg, pts, stereo=None, at=None):
    svg.arrow(pts, head="open", dash="6,4", size=10)
    if stereo:
        svg.text(at[0], at[1], stereo, size=11)


def realize(svg, pts):
    svg.arrow(pts, head="hollow", dash="6,4", size=12)


def compose(svg, pts, m_end=None, m_at=None, name=None, name_at=None):
    """Composition: filled diamond at pts[0] (the whole)."""
    svg.arrow(pts, head="open", tail="diamond", size=10)
    if m_end:
        svg.text(m_at[0], m_at[1], m_end, size=11)
    if name:
        svg.text(name_at[0], name_at[1], name, size=11)


def membership():
    svg = SVG(1330, 840)
    title(svg, "Membership Management - Updated Class Diagram (owner: Mahmoud Emad)")
    ilk = class_box(svg, 30, 60, "IMemberLookup", ops=["+exists(memberId: String): boolean"],
                    kind="interface", stereo="«interface»")
    proc = class_box(svg, 400, 60, "RenewalProcessor",
                     attrs=["-memberLookup: IMemberLookup", "-store: IMembershipStore",
                            "-renewalFeed: IRenewalFeed", "-clock: Clock"],
                     ops=["+renew(memberId: String, revisedExpiry: LocalDate, staffId: String): RenewalRecord"],
                     stereo="«control»")
    irf = class_box(svg, 1010, 60, "IRenewalFeed", ops=["+publish(change: RenewalChanged): void"],
                    kind="interface", stereo="«interface»")
    mpc = class_box(svg, 30, 220, "MemberProfileClient", attrs=["-baseUrl: String"],
                    ops=["+exists(memberId: String): boolean"], stereo="«adapter»", fill=ADAPTER)
    rob = class_box(svg, 1010, 220, "RenewalOutbox", attrs=["-table: String"],
                    ops=["+publish(change: RenewalChanged): void"], stereo="«adapter»", fill=ADAPTER)
    ims = class_box(svg, 30, 390, "IMembershipStore",
                    ops=["+findByMemberId(memberId: String): Optional<Membership>",
                         "+saveRenewal(m: Membership, r: RenewalRecord): void"],
                    kind="interface", stereo="«interface»")
    mem = class_box(svg, 520, 330, "Membership",
                    attrs=["-memberId: String", "-whatsappNumber: String", "-startDate: LocalDate",
                           "-expiryDate: LocalDate", "-status: MembershipStatus"],
                    ops=["+restore(...): Membership {static}", "+recordSubscription(start, expiry, today): void",
                         "+checkExpiry(today): MembershipStatus",
                         "+renew(revisedExpiry, staffId, now, today): RenewalRecord",
                         "+changeWhatsappNumber(number: String): void"],
                    stereo="«entity»")
    sql = class_box(svg, 30, 620, "SqlMembershipStore", attrs=['-database = "gymarena_membership"'],
                    ops=["+findByMemberId(memberId)", "+saveRenewal(m, r)"], stereo="«adapter»", fill=ADAPTER)
    sts = class_box(svg, 470, 660, "MembershipStatus", attrs=["NO_SUBSCRIPTION", "ACTIVE", "EXPIRED"],
                    kind="enum", stereo="«enumeration»")
    rr = class_box(svg, 700, 640, "RenewalRecord",
                   attrs=["+memberId: String", "+previousExpiry: LocalDate", "+revisedExpiry: LocalDate",
                          "+recordedBy: String", "+recordedAt: Instant"], kind="record", stereo="«record»")
    rc = class_box(svg, 1010, 640, "RenewalChanged",
                   attrs=["+memberId: String", "+previousExpiry: LocalDate", "+revisedExpiry: LocalDate"],
                   ops=["+from(record: RenewalRecord): RenewalChanged"], kind="record", stereo="«record»")

    y = ilk.cy
    assoc(svg, [(proc.x, y), (ilk.x + ilk.w, y)], "memberLookup", "1", (ilk.x + ilk.w + 8, y - 6),
          (ilk.x + ilk.w + 8, y + 15))
    y = irf.cy
    assoc(svg, [(proc.x + proc.w, y), (irf.x, y)], "renewalFeed", "1", (proc.x + proc.w + 8, y - 6),
          (irf.x - 14, y + 15))
    x = proc.x + 40
    assoc(svg, [(x, proc.y + proc.h), (x, ims.y + 25), (ims.x + ims.w, ims.y + 25)], "store", "1",
          (x + 6, proc.y + proc.h + 40), (ims.x + ims.w + 6, ims.y + 20))
    assoc(svg, [(mem.cx, proc.y + proc.h), (mem.cx, mem.y)], "renews", None, (mem.cx + 6, mem.y - 12))
    yy = ims.y + ims.h - 12
    svg.line(ims.x + ims.w, yy, mem.x, yy)
    svg.text(ims.x + ims.w + 8, yy - 5, "stores", size=11)
    svg.text(mem.x - 28, yy - 5, "0..*", size=11)
    svg.text(ims.x + ims.w + 8, yy + 14, "1", size=11)
    realize(svg, [(mpc.x + 60, mpc.y), (mpc.x + 60, ilk.y + ilk.h)])
    realize(svg, [(rob.x + 60, rob.y), (rob.x + 60, irf.y + irf.h)])
    realize(svg, [(sql.x + 60, sql.y), (sql.x + 60, ims.y + ims.h)])
    xs = sts.x + 60
    assoc(svg, [(xs, mem.y + mem.h), (xs, sts.y)], "-status", "1", (xs + 6, mem.y + mem.h + 22),
          (xs + 6, sts.y - 6))
    xr = rr.x + 80
    dep(svg, [(xr, mem.y + mem.h), (xr, rr.y)], "«create»", (xr + 6, mem.y + mem.h + 22))
    dep(svg, [(rc.x, rc.y + 70), (rr.x + rr.w, rc.y + 70)], "«from»", (rr.x + rr.w + 6, rc.y + 64))
    xd = 980
    dep(svg, [(proc.x + proc.w, proc.y + proc.h - 20), (xd, proc.y + proc.h - 20), (xd, rc.y + 20),
              (rc.x, rc.y + 20)], "«create»", (xd + 6, 560))
    note(svg, 30, 780, ["«adapter» (grey) = realized in services/membership-service (Python) and replaced",
                        "by a Mockito mock in RenewalProcessorTest. Other classes: domain-java/.../membership/"])
    return svg.save(os.path.join(OUT, "class_membership"))


def session():
    svg = SVG(1400, 960)
    title(svg, "Session Management - Updated Class Diagram (owner: Ahmed Ebrahim)")
    itc = class_box(svg, 30, 60, "ITrackingControl",
                    ops=["+isTrackingReliable(sessionId: String): boolean", "+pauseCounting(sessionId: String): void",
                         "+resumeCounting(sessionId: String): void"], kind="interface", stereo="«interface»")
    lc = class_box(svg, 470, 60, "SessionLifecycle",
                   attrs=["-store: ISessionStore", "-tracking: ITrackingControl",
                          "-recoveryPolicy: RecoveryPolicy", "-clock: Clock"],
                   ops=["+startSession(sessionId: String): SessionStatus",
                        "+onTrackingLost(sessionId: String, position: String): SessionStatus",
                        "+confirmAssignments(sessionId: String): SessionStatus",
                        "+reportDiscomfort(sessionId: String): SessionStatus"], stereo="«control»")
    rp = class_box(svg, 1040, 60, "RecoveryPolicy",
                   ops=["+shouldPause(s: ChallengeSession): boolean",
                        "+canResume(s, reliable, confirmed): boolean"])
    tcl = class_box(svg, 30, 230, "TrackingClient", attrs=["-baseUrl: String"],
                    ops=["+isTrackingReliable(...)", "+pauseCounting(...)", "+resumeCounting(...)"],
                    stereo="«adapter»", fill=ADAPTER)
    iss = class_box(svg, 30, 430, "ISessionStore",
                    ops=["+findById(sessionId: String): Optional<ChallengeSession>",
                         "+save(session: ChallengeSession): void"], kind="interface", stereo="«interface»")
    sql = class_box(svg, 30, 590, "SqlSessionStore", attrs=['-database = "gymarena_session"'],
                    ops=["+findById(...)", "+save(...)"], stereo="«adapter»", fill=ADAPTER)
    cs = class_box(svg, 560, 330, "ChallengeSession",
                   attrs=["-sessionId: String", "-mode: SessionMode", "-status: SessionStatus",
                          "-accumulatedActive: Duration", "-activeSince: Instant"],
                   ops=["+start(allPositionsReliable: boolean, now: Instant): void",
                        "+addRepetition(memberId: String): void",
                        "+pause(reason: InterruptionReason, position: String, now: Instant): void",
                        "+resume(reliable: boolean, confirmed: boolean, now: Instant): void",
                        "+complete(now: Instant): void", "+stopForDiscomfort(now: Instant): void",
                        "+closeIncomplete(): void", "+activeTime(now: Instant): Duration",
                        "+allTargetsReached(): boolean"], stereo="«entity»")
    st = class_box(svg, 1180, 330, "SessionStatus",
                   attrs=["CREATED", "ACTIVE", "PAUSED", "COMPLETED", "STOPPED", "INCOMPLETE"],
                   ops=["+isFinal(): boolean"], kind="enum", stereo="«enumeration»")
    md = class_box(svg, 1180, 560, "SessionMode", attrs=["SOLO", "LOCAL_1V1"], kind="enum",
                   stereo="«enumeration»")
    sp = class_box(svg, 300, 740, "SessionParticipant",
                   attrs=["-memberId: String", "-position: String", "-acceptedRepetitions: int"],
                   ops=["~addRepetition(): void"])
    rs = class_box(svg, 600, 740, "RuleSnapshot",
                   attrs=["+exercise: String", "+level: int", "+targetRepetitions: int", "+timeLimit: Duration",
                          "+ruleVersion: int", "+ranked: boolean"], kind="record", stereo="«record»")
    si = class_box(svg, 860, 740, "SessionInterruption",
                   attrs=["+reason: InterruptionReason", "+position: String", "+at: Instant"],
                   kind="record", stereo="«record»")
    ir = class_box(svg, 1140, 740, "InterruptionReason",
                   attrs=["TRACKING_LOST", "POSITION_SWAP_UNCERTAIN", "DISCOMFORT"], kind="enum",
                   stereo="«enumeration»")

    y = itc.cy
    assoc(svg, [(lc.x, y), (itc.x + itc.w, y)], "tracking", "1", (itc.x + itc.w + 8, y - 6),
          (itc.x + itc.w + 8, y + 15))
    y = rp.cy
    assoc(svg, [(lc.x + lc.w, y), (rp.x, y)], "recoveryPolicy", "1", (lc.x + lc.w + 6, y - 6),
          (rp.x - 14, y + 15))
    x = lc.x + 40
    assoc(svg, [(x, lc.y + lc.h), (x, iss.y + 25), (iss.x + iss.w, iss.y + 25)], "store", "1",
          (x + 6, lc.y + lc.h + 30), (iss.x + iss.w + 6, iss.y + 20))
    xm = cs.x + 120
    assoc(svg, [(xm, lc.y + lc.h), (xm, cs.y)], "manages", None, (xm + 6, cs.y - 12))
    yy = iss.y + iss.h - 10
    svg.line(iss.x + iss.w, yy, cs.x, yy)
    svg.text(iss.x + iss.w + 8, yy - 5, "stores", size=11)
    svg.text(cs.x - 28, yy - 5, "0..*", size=11)
    xp = rp.x + 40
    dep(svg, [(xp, rp.y + rp.h), (xp, cs.y + 40), (cs.x + cs.w, cs.y + 40)], "«use»", (xp + 6, rp.y + rp.h + 30))
    realize(svg, [(tcl.x + 60, tcl.y), (tcl.x + 60, itc.y + itc.h)])
    realize(svg, [(sql.x + 60, sql.y), (sql.x + 60, iss.y + iss.h)])
    y = st.y + 60
    assoc(svg, [(cs.x + cs.w, y), (st.x, y)], "-status", "1", (cs.x + cs.w + 8, y - 6), (st.x - 14, y + 15))
    y = md.cy
    assoc(svg, [(cs.x + cs.w, y), (md.x, y)], "-mode", "1", (cs.x + cs.w + 8, y - 6), (md.x - 14, y + 15))
    ym = 700
    compose(svg, [(cs.x + 30, cs.y + cs.h), (cs.x + 30, ym), (sp.cx, ym), (sp.cx, sp.y)], "1..2",
            (sp.cx + 6, sp.y - 8), "participants", (sp.cx + 6, ym - 6))
    compose(svg, [(rs.cx + 10, cs.y + cs.h), (rs.cx + 10, rs.y)], "1", (rs.cx + 16, rs.y - 8), "rules",
            (rs.cx + 16, cs.y + cs.h + 30))
    xi = cs.x + cs.w - 30
    compose(svg, [(xi, cs.y + cs.h), (xi, ym), (si.cx, ym), (si.cx, si.y)], "0..*", (si.cx + 6, si.y - 8),
            "interruptions", (si.cx + 6, ym - 6))
    y = ir.y + 50
    assoc(svg, [(si.x + si.w, y), (ir.x, y)], "reason", "1", (si.x + si.w + 6, y - 6), (ir.x - 14, y + 15))
    note(svg, 30, 900, ["«adapter» (grey) = realized in services/session-service (Python) and replaced by a",
                        "Mockito mock in SessionLifecycleTest. Other classes: domain-java/.../session/"])
    return svg.save(os.path.join(OUT, "class_session"))


def member():
    svg = SVG(1350, 860)
    title(svg, "Member Management - Updated Class Diagram (owner: Mohamed Soliman)")
    ims = class_box(svg, 30, 60, "IMemberStore", ops=["+findById(memberId: String): Optional<MemberProfile>"],
                    kind="interface", stereo="«interface»")
    svc = class_box(svg, 450, 60, "MeasurementService",
                    attrs=["-memberStore: IMemberStore", "-measurementStore: IMeasurementStore",
                           "-scale: IScaleSource", "-clock: Clock"],
                    ops=["+captureReading(memberId: String): WeightReading",
                         "+confirmReading(readingId: String, memberId: String): WeightReading",
                         "+rejectReading(readingId: String): WeightReading"], stereo="«control»")
    iss = class_box(svg, 1040, 60, "IScaleSource", ops=["+readStableWeight(): ScaleReading"],
                    kind="interface", stereo="«interface»")
    ser = class_box(svg, 1040, 200, "SerialScaleAdapter", attrs=['-port: String'],
                    ops=["+readStableWeight(): ScaleReading"], stereo="«adapter»", fill=ADAPTER)
    ims2 = class_box(svg, 30, 270, "IMeasurementStore",
                     ops=["+nextReadingId(): String", "+findById(readingId: String): Optional<WeightReading>",
                          "+save(reading: WeightReading): void"], kind="interface", stereo="«interface»")
    sql = class_box(svg, 30, 470, "SqlMemberStore", attrs=['-database = "gymarena_member"'],
                    ops=["+findById(memberId)", "+nextReadingId()", "+findById(readingId)", "+save(reading)"],
                    stereo="«adapter»", fill=ADAPTER)
    wr = class_box(svg, 480, 340, "WeightReading",
                   attrs=["-readingId: String", "-memberId: String", "-weightKg: double", "-readAt: Instant",
                          "-status: ReadingStatus", "-confirmedAt: Instant"],
                   ops=["+capture(readingId, member, raw): WeightReading {static}",
                        "+confirm(confirmingMemberId: String, now: Instant): void", "+reject(): void"],
                   stereo="«entity»")
    sr = class_box(svg, 1040, 380, "ScaleReading",
                   attrs=["+weightKg: double", "+stable: boolean", "+readAt: Instant"],
                   ops=["+isValid(): boolean"], kind="record", stereo="«record»")
    rs = class_box(svg, 480, 660, "ReadingStatus", attrs=["PENDING_CONFIRMATION", "CONFIRMED", "DISCARDED"],
                   kind="enum", stereo="«enumeration»")
    mp = class_box(svg, 770, 640, "MemberProfile",
                   attrs=["+memberId: String", "+name: String", "+age: int", "+memberCode: String"],
                   kind="record", stereo="«record»")
    ex = class_box(svg, 1040, 640, "InvalidScaleReadingException", stereo="«exception»")

    y = ims.cy
    assoc(svg, [(svc.x, y), (ims.x + ims.w, y)], "memberStore", "1", (ims.x + ims.w + 8, y - 6),
          (ims.x + ims.w + 8, y + 15))
    y = iss.cy
    assoc(svg, [(svc.x + svc.w, y), (iss.x, y)], "scale", "1", (svc.x + svc.w + 8, y - 6), (iss.x - 14, y + 15))
    x = svc.x + 30
    assoc(svg, [(x, svc.y + svc.h), (x, ims2.y + 25), (ims2.x + ims2.w, ims2.y + 25)], "measurementStore", "1",
          (x + 6, svc.y + svc.h + 30), (ims2.x + ims2.w + 6, ims2.y + 20))
    xm = wr.cx
    assoc(svg, [(xm, svc.y + svc.h), (xm, wr.y)], "creates / confirms", None, (xm + 6, wr.y - 12))
    yy = ims2.y + ims2.h - 10
    svg.line(ims2.x + ims2.w, yy, wr.x, yy)
    svg.text(ims2.x + ims2.w + 8, yy - 5, "stores", size=11)
    svg.text(wr.x - 28, yy - 5, "0..*", size=11)
    realize(svg, [(ser.x + 60, ser.y), (ser.x + 60, iss.y + iss.h)])
    realize(svg, [(sql.x + 60, sql.y), (sql.x + 60, ims2.y + ims2.h)])
    realize(svg, [(sql.x, sql.y + 30), (15, sql.y + 30), (15, ims.cy), (ims.x, ims.cy)])
    y = sr.y + 50
    dep(svg, [(wr.x + wr.w, y), (sr.x, y)], "«use»", (wr.x + wr.w + 8, y - 6))
    xs = rs.x + 60
    assoc(svg, [(xs, wr.y + wr.h), (xs, rs.y)], "-status", "1", (xs + 6, wr.y + wr.h + 22), (xs + 6, rs.y - 6))
    xmp = mp.x + 60
    dep(svg, [(wr.x + wr.w - 40, wr.y + wr.h), (wr.x + wr.w - 40, 610), (xmp, 610), (xmp, mp.y)], "«use»",
        (xmp + 6, 604))
    xe = ex.x + 60
    yex = wr.y + wr.h - 30
    dep(svg, [(wr.x + wr.w, yex), (xe, yex), (xe, ex.y)], "«throws»", (xe + 6, yex + 40))
    note(svg, 30, 800, ["«adapter» (grey) = realized in services/member-service (Python) and replaced by a",
                        "Mockito mock in MeasurementServiceTest. Other classes: domain-java/.../member/"])
    return svg.save(os.path.join(OUT, "class_member"))


def challenge():
    svg = SVG(1330, 850)
    title(svg, "Challenge Management - Updated Class Diagram (owner: Mohamed Hegazy)")
    ics = class_box(svg, 30, 330, "IChallengeStore",
                    ops=["+findRuleVersion(ruleId: String): Optional<ChallengeRuleVersion>",
                         "+findApprovedRule(exercise: String, level: int): Optional<ChallengeRuleVersion>",
                         "+findCurrentLevel(memberId: String, exercise: String): Optional<Integer>",
                         "+saveApproval(approved, superseded): void",
                         "+saveRejection(rejected: ChallengeRuleVersion): void"],
                    kind="interface", stereo="«interface»")
    cp = class_box(svg, 430, 60, "ChallengePlanner",
                   attrs=["-store: IChallengeStore", "-memberLookup: IMemberLookup", "-clock: Clock"],
                   ops=["+approveRules(ruleId: String, trainerId: String): ChallengeRuleVersion",
                        "+rejectRules(ruleId: String, trainerId: String, reason: String): ChallengeRuleVersion",
                        "+presentRules(memberId: String, exercise: String): RuleSummary"], stereo="«control»")
    iml = class_box(svg, 1040, 60, "IMemberLookup", ops=["+exists(memberId: String): boolean"],
                    kind="interface", stereo="«interface»")
    mpc = class_box(svg, 1040, 200, "MemberProfileClient", attrs=["-baseUrl: String"],
                    ops=["+exists(memberId: String): boolean"], stereo="«adapter»", fill=ADAPTER)
    sql = class_box(svg, 30, 600, "SqlChallengeStore", attrs=['-database = "gymarena_challenge"'],
                    ops=["+findRuleVersion(...)", "+findApprovedRule(...)", "+findCurrentLevel(...)",
                         "+saveApproval(...)", "+saveRejection(...)"], stereo="«adapter»", fill=ADAPTER)
    cr = class_box(svg, 620, 330, "ChallengeRuleVersion",
                   attrs=["-ruleId: String", "-exercise: String", "-level: int", "-version: int",
                          "-targetRepetitions: int", "-timeAllowance: Duration", "-completionPoints: int",
                          "-timeoutDeduction: int", "-winnerRule: WinnerRule", "-status: RuleStatus",
                          "-approvedBy: String", "-approvedAt: Instant"],
                   ops=["+approve(trainerId: String, now: Instant): void", "+reject(trainerId: String, reason: String): void",
                        "+supersede(now: Instant): void", "+summary(): RuleSummary"], stereo="«entity»")
    rs = class_box(svg, 1080, 360, "RuleStatus", attrs=["DRAFT", "APPROVED", "REJECTED", "SUPERSEDED"],
                   ops=["+isFinal(): boolean"], kind="enum", stereo="«enumeration»")
    wr = class_box(svg, 1080, 540, "WinnerRule", attrs=["MOST_REPETITIONS", "FIRST_TO_TARGET"], kind="enum",
                   stereo="«enumeration»")
    sm = class_box(svg, 620, 660, "RuleSummary",
                   attrs=["+exercise, +level, +version", "+targetRepetitions, +timeAllowance",
                          "+completionPoints, +timeoutDeduction, +winnerRule"], kind="record", stereo="«record»")
    y = iml.cy
    assoc(svg, [(cp.x + cp.w, y), (iml.x, y)], "memberLookup", "1", (cp.x + cp.w + 8, y - 6), (iml.x - 14, y + 15))
    x = cp.x + 40
    assoc(svg, [(x, cp.y + cp.h), (x, ics.y)], "store", "1", (x + 6, cp.y + cp.h + 30), (x + 6, ics.y - 6))
    xm = cr.x + 170
    assoc(svg, [(xm, cp.y + cp.h), (xm, cr.y)], "approves / supersedes / presents", None, (xm + 6, cr.y - 12))
    yy = ics.y + ics.h - 12
    svg.line(ics.x + ics.w, yy, cr.x, yy)
    svg.text(ics.x + ics.w + 8, yy - 5, "stores", size=11)
    svg.text(cr.x - 28, yy - 5, "0..*", size=11)
    realize(svg, [(mpc.x + 60, mpc.y), (mpc.x + 60, iml.y + iml.h)])
    realize(svg, [(sql.x + 60, sql.y), (sql.x + 60, ics.y + ics.h)])
    y = rs.y + 50
    assoc(svg, [(cr.x + cr.w, y), (rs.x, y)], "-status", "1", (cr.x + cr.w + 8, y - 6), (rs.x - 14, y + 15))
    y = wr.cy
    assoc(svg, [(cr.x + cr.w, y), (wr.x, y)], "-winnerRule", "1", (cr.x + cr.w + 8, y - 6), (wr.x - 14, y + 15))
    xs = sm.x + 80
    dep(svg, [(xs, cr.y + cr.h), (xs, sm.y)], "«create»", (xs + 6, cr.y + cr.h + 20))
    note(svg, 470, 790, ["«adapter» (grey) = realized in services/challenge-service (Python) and replaced by a",
                        "Mockito mock in ChallengePlannerTest. Other classes: domain-java/.../challenge/"])
    return svg.save(os.path.join(OUT, "class_challenge"))


if __name__ == "__main__":
    for fn in (membership, session, member, challenge):
        print(fn())
