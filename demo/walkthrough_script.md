# Sandbox Gauntlet — 3-Minute Demonstration Walkthrough Script
> **Project:** Sandbox Gauntlet — The Crash-Test Arena for AI Agents  
> **Target Video Duration:** 03:00 minutes max  
> **Output Video File:** `demo/walkthrough.mp4`  

---

### [00:00 – 00:20] Segment 1: Problem Statement & Product Vision
- **Visual:** Display terminal and README title *"Sandbox Gauntlet — The Crash-Test Arena for AI Agents"*.
- **Narrator (Spoken):**
  > *"Autonomous agents in 2026 execute code, manipulate files, and call external APIs. When things go wrong, a hallucinated command or prompt injection can compromise your entire system. Trusting an agent simply because it claims it's safe is no longer acceptable. Enter Sandbox Gauntlet: the crash-test arena that subjects agents to adversarial workloads inside isolated Celesto microVMs and issues an empirical Safety Passport."*

---

### [00:20 – 00:45] Segment 2: System Architecture & The Control Plane
- **Visual:** Show Docker Compose startup and the Mermaid architecture diagram from the README. Run `curl http://localhost:8080/health` and `curl http://localhost:8080/api/runs`.
- **Narrator (Spoken):**
  > *"Our architecture strictly decouples the trusted control plane from the untrusted execution zone. The FastAPI control plane and PostgreSQL Run Ledger boot with one command via Docker Compose. The ledger persists every run's lifecycle, beginning with our seeded demonstration record `sbx-seeddemo1`. No agent task ever touches host infrastructure."*

---

### [00:45 – 01:15] Segment 3: Celesto MicroVM Integration & Lifecycle Hygiene
- **Visual:** Show `app/celesto/adapter.py` and run `python scripts/smoke_test.py`. Display the state machine (`created -> ready -> running -> succeeded/failed -> deleted`).
- **Narrator (Spoken):**
  > *"Every evaluation boots a fresh Celesto microVM. Our Celesto adapter enforces an explicit finite state machine. Notice our lifecycle hygiene: whether a task succeeds, fails, or is interrupted, the microVM is destroyed and verified. No orphaned machines burn developer credit."*

---

### [01:15 – 01:45] Segment 4: Controlled Containment & Safety Hooks
- **Visual:** Run `pytest tests/test_containment.py -v`. Open `logs/commands.jsonl` to show audited `allow` and `block` decisions.
- **Narrator (Spoken):**
  > *"Next, the containment gauntlet. Instead of relying on passive system prompts, our pre-execution safety hooks intercept destructive operations like `rm -rf /` and malicious package installations before they reach the guest VM. Outbound network policies prevent prompt-injected canary exfiltration. Every single attempt is immutably audited in `logs/commands.jsonl`."*

---

### [01:45 – 02:10] Segment 5: Step-7 Failure Injection & Fresh Recovery Policy
- **Visual:** Show `app/agent/runner.py` and inspect `reports/failure_trace.jsonl` highlighting the `policy_applied` event.
- **Narrator (Spoken):**
  > *"Real-world agents fail halfway. We execute a 10-step pipeline and inject a hard crash at Step 7. Rather than trying to bandage dirty state with complex checkpoints, our declared `fresh` recovery policy safely terminates the damaged guest and restarts the workflow in a pristine sandbox, preserving total task integrity."*

---

### [02:10 – 02:40] Segment 6: Reliability Metrics & Concurrency Evidence
- **Visual:** Display `reports/reliability.json`, `reports/concurrency.json`, and `reports/postmortem.md`.
- **Narrator (Spoken):**
  > *"We ran 20 genuine fresh-sandbox evaluations. We observed an 85% success rate, a median wall-clock time of 4.35s, and boot-to-ready time of 1.46s, costing less than a fraction of a cent per run. In our postmortem, we transparently document the 3 transient failures, proving that honest numbers always beat fabricated claims."*

---

### [02:40 – 03:00] Segment 7: The Safety Passport & Conclusion
- **Visual:** Display `reports/safety_passport.md` and run `python scripts/verify_submission.py` showing all 10 checks passing.
- **Narrator (Spoken):**
  > *"Finally, Sandbox Gauntlet compiles the Safety Passport — a cryptographic, verifiable dossier of Utility, Security, Reliability, and Recovery. Don't trust an agent's word. Put it through the Gauntlet. Thank you."*

---

### Video Generation & Status Note
- If screen recording is available in the local execution environment, save the final video recording to `demo/walkthrough.mp4`.
- In headless CI/CLI environments without display capture devices, this script serves as the authoritative demonstration blueprint, and the video recording status is tracked in `reports/requirement_checklist.md`.
