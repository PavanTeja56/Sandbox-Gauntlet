-- Initialize the Run Ledger schema and insert the seed record
CREATE TABLE IF NOT EXISTS runs (
    run_id VARCHAR(128) PRIMARY KEY,
    sandbox_name VARCHAR(128) NOT NULL,
    problem_id VARCHAR(128) NOT NULL,
    state VARCHAR(32) NOT NULL,
    execution_target VARCHAR(64) NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Seed row sbx-seeddemo1 as required by the specification
-- Re-running the SQL does not duplicate it
INSERT INTO runs (run_id, sandbox_name, problem_id, state, execution_target, created_at)
VALUES (
    'seed-run-001',
    'sbx-seeddemo1',
    'seed_demonstration',
    'deleted',
    'celesto_sandbox',
    CURRENT_TIMESTAMP
)
ON CONFLICT (run_id) DO NOTHING;
