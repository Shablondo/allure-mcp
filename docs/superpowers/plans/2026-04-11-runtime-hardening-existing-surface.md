# Runtime Hardening Existing Surface Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Harden the existing Allure TestOps MCP runtime for correctness and stability without adding new MCP methods.

**Architecture:** Keep the public MCP tool surface unchanged while improving the shared HTTP client lifecycle, retry/circuit breaker behavior, cache invalidation, config-based `projectId` fallback, and README accuracy. Drive the behavior changes with focused pytest coverage around the client and selected controllers.

**Tech Stack:** Python 3.10+, FastMCP, httpx, pytest, asyncio, tenacity

---

### Task 1: Establish test harness

**Files:**
- Create: `tests/test_client.py`
- Create: `tests/test_project_id_fallback.py`
- Modify: `pyproject.toml`

- [ ] Add pytest as a development dependency target and create focused tests for retry, circuit breaker, cache invalidation, and `projectId` fallback behavior.
- [ ] Run the new tests to confirm they fail against current behavior.

### Task 2: Harden shared HTTP client behavior

**Files:**
- Modify: `src/allure_testops_mcp/client.py`
- Test: `tests/test_client.py`

- [ ] Refactor the client to use a shared `httpx.AsyncClient`, restrict retry behavior to transient/network failures, and make half-open circuit breaker recovery allow only one probe request.
- [ ] Replace global full-cache wipes with targeted invalidation that preserves unrelated GET results.
- [ ] Run client-focused tests until green.

### Task 3: Add config fallback without changing API shape

**Files:**
- Modify: `src/allure_testops_mcp/config.py`
- Modify: `src/allure_testops_mcp/controllers/_utils.py`
- Modify: selected controllers with optional `projectId`
- Test: `tests/test_project_id_fallback.py`

- [ ] Implement a helper that keeps current parameters and semantics, but fills missing optional `projectId` from config when the tool already supports omitting it.
- [ ] Preserve explicit user-provided `projectId` precedence.
- [ ] Run fallback tests until green.

### Task 4: Fix existing functional gaps without new methods

**Files:**
- Modify: `src/allure_testops_mcp/client.py`
- Modify: `src/allure_testops_mcp/controllers/test_case_attachment_controller.py`
- Modify: `src/allure_testops_mcp/controllers/test_case_controller.py`
- Modify: `src/allure_testops_mcp/controllers/test_case_tag_controller.py`
- Modify: `README.md`

- [ ] Fix existing problematic behavior and stale guidance in descriptions/README so documented flows match current implementation.
- [ ] Keep the existing method set intact; only repair current capabilities and wording.
- [ ] Run compile/test verification.

### Task 5: Final verification

**Files:**
- Modify: `README.md`

- [ ] Run `python3 -m pytest` for the new test suite.
- [ ] Run `python3 -m compileall src`.
- [ ] Review the diff for accidental surface-area expansion before closing.
