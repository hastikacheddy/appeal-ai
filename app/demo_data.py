"""A recorded sample run on the fictional letter in samples/. Used only when API keys
are missing (or DEMO_MODE=on) so anyone can click through the experience.
The UI labels these results as a sample. Insurer, patient and IDs are fictional."""
from __future__ import annotations

import asyncio


from . import config, deadlines

DENIAL_DATE = "2026-10-06"  # matches samples/sample_denial.png

FACTS = {
    "insurer": "Northwind Health Plan (fictional)",
    "plan_name": "Northwind Silver PPO",
    "plan_type": "employer_or_aca",
    "state": "Illinois",
    "member_name": "Jordan Rivera",
    "member_id": "NWH-448210937",
    "claim_number": "PA-2026-0918-5521",
    "provider": "Lakeside Spine & Orthopedics",
    "service": "MRI lumbar spine without contrast",
    "codes": ["CPT 72148", "ICD-10 M54.16"],
    "date_of_service": None,
    "denial_date": DENIAL_DATE,
    "appeal_deadline": None,
    "denial_reason_quote": "The requested imaging is not medically necessary. Clinical guidelines recommend a trial of at least 6 weeks of conservative therapy prior to advanced imaging for low back pain.",
    "policy_cited": "Northwind Clinical Policy RAD-114: Advanced Imaging of the Spine",
    "appeal_address": "Northwind Health Plan, Appeals Unit, PO Box 0000, Chicago, IL",
    "appeal_fax": None,
    "urgent": False,
}

TRIAGE = {
    "category": "medical_necessity",
    "category_label": "Medical necessity (prior authorization)",
    "plain_english": "Northwind says the MRI isn't needed yet because you haven't tried six weeks of non-surgical treatment. If your records show you already did, or that you have warning signs like worsening leg weakness, that reason doesn't hold.",
    "appeal_path": [
        "Internal appeal to Northwind (this letter)",
        "Ask your doctor for a peer-to-peer review with Northwind's medical reviewer",
        "If upheld: request independent external review (Illinois Department of Insurance)",
    ],
    "queries": [
        {"q": "Northwind Clinical Policy RAD-114 lumbar spine MRI criteria", "kind": "policy"},
        {"q": "ACR Appropriateness Criteria low back pain radiculopathy MRI after conservative therapy", "kind": "clinical"},
        {"q": "MRI lumbar spine progressive neurologic deficit red flags guideline", "kind": "clinical"},
        {"q": "ACA internal appeal rights full and fair review claim file", "kind": "rules"},
        {"q": "Illinois external review health insurance denial", "kind": "rules"},
    ],
}

SOURCES = [
    {"id": 1, "kind": "clinical", "title": "An image-based review of the ACR Appropriateness Criteria for Low Back Pain",
     "url": "https://appliedradiology.com/articles/an-image-based-review-of-the-acr-appropriateness-criteria-for-low-back-pain",
     "content": "Summarises ACR guidance: MRI of the lumbar spine without contrast is usually appropriate for patients with persistent or progressive symptoms during or after 6 weeks of optimal medical management who are surgical or intervention candidates, and earlier when red flags or progressive neurologic deficit are present."},
    {"id": 2, "kind": "rules", "title": "Internal appeals | HealthCare.gov",
     "url": "https://www.healthcare.gov/how-do-i-appeal-a-health-insurance-companys-decision/internal-appeals/",
     "content": "If your claim is denied you can ask your insurer to conduct a full and fair review of its decision. You must file within 180 days of receiving notice that your claim was denied. If your case is urgent, the insurer must speed up the process."},
    {"id": 3, "kind": "rules", "title": "Appealing health plan decisions | HealthCare.gov",
     "url": "https://www.healthcare.gov/appeal-insurance-company-decision/",
     "content": "You have the right to appeal an insurer's decision. Internal appeal: ask the insurer to review its decision. External review: have an independent third party review it; the insurer no longer gets the final say."},
    {"id": 4, "kind": "rules", "title": "Has Your Health Insurer Denied Payment for a Medical Service? You Have a Right to Appeal | CMS",
     "url": "https://www.cms.gov/CCIIO/Resources/Fact-Sheets-and-FAQs/appeals06152012a",
     "content": "Your plan must tell you why it denied your claim and how to appeal. You have the right to see your file and present evidence and testimony as part of the appeals process."},
]

STRATEGY = {
    "strength": 4,
    "strength_reason": "Strong if Dr. Okafor's notes document 6+ weeks of physical therapy and the new foot weakness; both directly meet the guideline the denial relies on.",
    "arguments": [
        {"title": "The conservative-therapy requirement is already met",
         "point": "The denial assumes no trial of conservative care. Jordan completed 7 weeks of supervised physical therapy and NSAIDs starting in August, with persistent symptoms. That satisfies the 6-week threshold the insurer itself cites.",
         "cites": [1]},
        {"title": "Progressive neurologic deficit justifies imaging now",
         "point": "New left foot dorsiflexion weakness (4/5) and worsening radicular pain are red-flag findings. Guidelines support MRI without waiting when deficits progress, and Jordan is being evaluated for intervention.",
         "cites": [1]},
        {"title": "The denial does not apply the plan's own criteria to this patient",
         "point": "The letter quotes a generic guideline but does not address the documented therapy or exam findings. A full and fair review requires engaging with the submitted evidence.",
         "cites": [2, 4]},
    ],
    "insurer_weaknesses": [
        "Boilerplate reason that ignores the submitted PT records",
        "No reviewer name or specialty listed",
        "Policy RAD-114 criteria not quoted or attached",
    ],
    "evidence_to_gather": [
        {"item": "Physical therapy notes with dates (Aug 4 - Sep 22)", "from": "doctor", "why": "Proves the 6-week conservative-therapy requirement"},
        {"item": "Exam note documenting 4/5 dorsiflexion weakness", "from": "doctor", "why": "Shows progressive neurologic deficit"},
        {"item": "Letter of medical necessity from Dr. Okafor", "from": "doctor", "why": "Clinician's direct statement carries the most weight"},
        {"item": "Copy of Northwind Clinical Policy RAD-114", "from": "insurer", "why": "Lets you quote their own criteria back to them"},
    ],
    "ask_for": [
        "The complete claim file, including all documents considered",
        "The exact clinical criteria (RAD-114) applied",
        "Name and board specialty of the reviewing clinician",
        "A peer-to-peer review between Dr. Okafor and the reviewer",
    ],
}

LETTER = """**Jordan Rivera**
[Street Address] · [City, State ZIP] · [Phone] · [Email]

[Date]

Northwind Health Plan — Appeals Unit
PO Box 0000, Chicago, IL

**Re: Request for internal appeal — Member ID NWH-448210937 — Claim/Authorization PA-2026-0918-5521**
**Service: MRI lumbar spine without contrast (CPT 72148), ordered by Lakeside Spine & Orthopedics**

To the Appeals Unit:

I am writing to appeal Northwind's denial of prior authorization for a lumbar spine MRI, dated """ + DENIAL_DATE + """. The denial states the imaging is not medically necessary because guidelines recommend at least 6 weeks of conservative therapy first. I ask for a full and fair review of this decision [2].

**1. I have already completed more than 6 weeks of conservative therapy.**
From August 4 to September 22 I completed 7 weeks of supervised physical therapy and took prescribed anti-inflammatory medication. My symptoms persisted. Recognized imaging guidelines consider lumbar MRI appropriate when symptoms persist after 6 weeks of medical management in a patient being considered for intervention [1]. The enclosed therapy records document this.

**2. My neurologic symptoms are getting worse.**
My physician has documented new weakness in my left foot (dorsiflexion 4/5) and worsening pain radiating down my leg. Progressive neurologic deficit is a recognized reason to image without further delay [1]. I am being evaluated for intervention, which requires this MRI.

**3. The denial does not address my records.**
The denial repeats a general guideline but does not engage with the therapy history and exam findings my provider submitted. I have the right to present evidence and to a review that considers it [2][4].

**Requests**
Please provide, free of charge: (a) my complete claim file; (b) the full text of Clinical Policy RAD-114 and the specific criteria applied; and (c) the name and specialty of the clinician who reviewed my request. My physician, Dr. Okafor, is available for a peer-to-peer review at [phone].

I ask that Northwind overturn this denial and authorize the MRI. If the denial is upheld, I intend to request an independent external review [3].

Sincerely,

Jordan Rivera

*Enclosures: denial letter; physical therapy notes; physician exam notes; letter of medical necessity*"""

DOCTOR = """**Letter of Medical Necessity — template for Dr. [Name]**

Re: [Patient name], DOB [__], Member ID NWH-448210937 — MRI lumbar spine w/o contrast (CPT 72148)

I am the treating [specialty] for [patient]. They present with [duration] of low back pain radiating to the [left] leg, consistent with [L5 radiculopathy, ICD-10 M54.16].

Conservative management: [7] weeks of supervised physical therapy ([dates]) and [medication/dose], without adequate improvement.

Current findings: [dorsiflexion weakness 4/5, diminished reflex, positive straight-leg raise at __°], which have progressed since [date].

MRI is required to evaluate for [nerve root compression] and to plan [epidural injection / surgical consultation]. Delay risks [permanent motor deficit]. This request is consistent with recognized imaging guidelines for persistent radiculopathy after 6 weeks of conservative care and for progressive neurologic deficit.

I am available for peer-to-peer review at [phone].

[Signature, credentials, NPI]"""

VERIFY = {"checked": 6, "supported": 6, "issues": []}


async def replay():
    deadline = deadlines.compute(FACTS["denial_date"], None, FACTS["plan_type"])
    steps = [
        ("read", config.MODEL_VISION, "Reading 1 page image(s)", FACTS),
        ("triage", config.MODEL_FAST, "Classifying the denial", {**TRIAGE, "deadline": deadline}),
        ("research", "Tavily", "Running 5 searches", {"sources": SOURCES}),
        ("strategy", config.MODEL_ULTRA, "Building the argument from evidence", STRATEGY),
        ("draft", config.MODEL_SUPER, "Writing your appeal letter", None),
        ("verify", config.MODEL_SUPER, "Checking every citation", VERIFY),
    ]
    pauses = {"read": 1.4, "triage": 0.9, "research": 1.6, "strategy": 2.4, "draft": 1.8, "verify": 1.0}
    ledger = []
    for sid, model, detail, data in steps:
        running = {"type": "step", "id": sid, "status": "running", "model": model, "detail": detail}
        if sid == "research":
            running["data"] = {"queries": TRIAGE["queries"]}
        yield running
        await asyncio.sleep(pauses[sid])
        yield {"type": "step", "id": sid, "status": "done", "model": model, **({"data": data} if data else {})}
        if model != "Tavily":
            ledger.append({"step": sid, "model": model, "prompt_tokens": 0, "completion_tokens": 0, "seconds": pauses[sid]})
    yield {"type": "result", "facts": FACTS, "triage": TRIAGE, "deadline": deadline, "sources": SOURCES,
           "strategy": STRATEGY, "letter": LETTER, "doctor_letter": DOCTOR, "verification": VERIFY,
           "ledger": ledger, "demo": True}
