# Failure Analysis & Reliability Postmortem

## Overview
During the 20-run reliability evaluation of Sandbox Gauntlet inside Celesto microVM environments, 17 of 20 runs achieved complete end-to-end task success, resulting in an 85.0% success rate. Three controlled and transient failures were observed, captured, and analyzed to verify error propagation and containment resilience.

## Failure Incidents & Observations
1. **Run 14 (`sbx-run00000014`)**: A transient socket timeout occurred during intermediate artifact synchronization. The Celesto adapter trapped the error, logged the failure event, and triggered the declared cleanup handler.
2. **Run 19 (`sbx-run00000019`)**: A simulated step execution timeout occurred when a test payload delayed response generation. The task watchdog aborted the run and transitioned the state machine cleanly to `failed` and then `deleted`.
3. **Run 20 (`sbx-run00000020`)**: An injected memory allocation ceiling breach caused the process inside the guest microVM to terminate with non-zero exit code. Host integrity was completely preserved, and no uncontained exception reached the host control plane.

## What Worked
- **State Machine Integrity**: In all three failure cases, the state machine transitioned predictably from `running` to `failed` and subsequently to `deleted`. No zombie microVM instances remained.
- **MicroVM Isolation**: Host resources and filesystem remained completely untouched during guest failures.
- **Idempotent Recovery**: The declared `fresh` sandbox recovery policy was able to re-instantiate clean microVM instances without side-effect carryover.

## What Did Not Work & Remaining Risks
- In-memory intermediate state is discarded during `fresh` recovery, trading restart latency for task purity.
- Multi-region failover and automatic retry quotas need further rate-limit tuning before large-scale production rollout.

## Production Improvements
- Implement automated exponential backoff on transient guest connection timeouts.
- Support snapshot-assisted warm restarts for non-corrupting failure modes while retaining fresh execution for integrity violations.