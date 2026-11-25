# Designing Restartable Data Migrations

> This is general technical guidance using synthetic examples and public references. It is not an account of a particular employer, client, project or production migration.

## Why restartability matters

A data migration can be logically correct and still be operationally unsafe. Long-running work can be interrupted by capacity limits, deployment windows, connection failures, lock contention or incorrect assumptions about legacy state.

A restartable migration should normally resume by rerunning the same operation and re-evaluating durable target state. Completed work is not duplicated, conflicts remain visible, and the migration does not depend on knowing the exact interruption point. Manual correction may still be required for states the convergence rules deliberately reject.

## Define target-state invariants

Start with invariants, not insert statements. For a parent-child migration, invariants might be:

- Every eligible parent has one authoritative target container.
- Every target container has at most one target child for a semantic key.
- Every required single-valued property has one authoritative current value.
- Existing valid data is reused.
- Conflicting legacy state is reported or resolved through a documented rule.

These rules must account for more than two states. Real data can contain no row, one correct row, one incorrect row, multiple valid candidates or contradictory rows.

## Build a deterministic worklist

Select work through stable keys and deterministic keyset ordering. If eligibility must be fixed for the run, materialize the immutable source keys and record the selection boundary. Do not treat a previewed action as current truth.

```text
Eligible parent key
-> observed state for reporting
-> intended target state
-> proposed action: skip, insert, update, resolve conflict or reject
```

Before writing each unit, re-read and classify its target state inside the transaction and under the selected concurrency control. Deterministic ordering makes traversal reproducible; by itself it does not prevent skips, repeats or stale decisions when concurrent data changes.

## Separate dry-run and execution modes

A useful dry run reports:

- Eligible row count.
- Rows already in the target state.
- Rows requiring inserts or updates.
- Ambiguous rows that cannot be resolved automatically.
- Estimated write volume.
- Preconditions such as free capacity and required indexes.

The execution mode should consume the same state-classification logic. Duplicating the rules in separate preview and write scripts creates drift exactly where confidence is most important.

## Converge instead of blindly inserting

For each parent, inspect all candidate containers before selecting one:

1. Reuse a container that already holds the target child.
2. Otherwise choose one valid container using a documented stable tie-breaker.
3. Create a container only when no valid container exists.
4. Insert the target child only when the semantic relationship is absent.
5. For a single-valued property, skip an exact match, update through the supported model path when the value conflicts, and insert only when no authoritative row exists.

This is convergence: every accepted starting state has a defined path to one target state.

## Make check-and-write atomic

An existence check followed by an insert is not concurrency-safe by itself. Two sessions can both observe absence and then create duplicates.

Use one or more controls whose enforcement can be demonstrated:

- Enforce single-writer execution technically, for example with a transaction- or session-owned application lock, while blocking or routing every competing writer.
- Prefer a unique constraint or unique index when the semantic uniqueness rule is permanent and can be expressed by the schema.
- In SQL Server, protect an absent-row lookup and its write in one transaction using a tested `SERIALIZABLE` or `HOLDLOCK` strategy against an index whose leading keys match the lookup predicate.
- If a uniqueness race can still occur, roll back the losing unit of work and re-read current state. Do not continue from the stale pre-insert result.
- Route all competing writes through the same atomic operation when schema enforcement is not possible.

Before adding uniqueness, detect and resolve existing duplicates and assess the locking, log and deployment impact. A maintenance window is useful operational coordination, but it is not a concurrency control unless effective write permissions or an equivalent lock enforce it.

## Choose recoverable transaction boundaries

One global transaction offers all-or-nothing semantics but may create excessive log growth, lock duration and rollback cost. One transaction per statement can leave a business unit partially updated.

A useful boundary is often one independently recoverable business unit, such as one parent and all required child/property changes.

In this example, the cursor visits one parent at a time so each parent’s changes can commit or roll back together; on restart, the migration checks the stored data rather than relying on the cursor position.

```sql
SET XACT_ABORT ON;

DECLARE @WorkId bigint;

DECLARE work_cursor CURSOR LOCAL FAST_FORWARD FOR
    SELECT WorkId
    FROM #MigrationWork
    WHERE Resolution = 'Automatic'
    ORDER BY WorkId;

OPEN work_cursor;
FETCH NEXT FROM work_cursor INTO @WorkId;

WHILE @@FETCH_STATUS = 0
BEGIN
    BEGIN TRY
        BEGIN TRANSACTION;

        -- Lock or otherwise protect the semantic target state.
        -- Resolve the authoritative container for @WorkId.
        -- Apply only missing or explicitly correctable changes.

        COMMIT TRANSACTION;
    END TRY
    BEGIN CATCH
        IF XACT_STATE() <> 0
            ROLLBACK TRANSACTION;

        INSERT INTO #MigrationErrors (WorkId, ErrorNumber)
        VALUES (@WorkId, ERROR_NUMBER());

        THROW; -- Fail closed unless a reviewed policy permits continuation.
    END CATCH;

    FETCH NEXT FROM work_cursor INTO @WorkId;
END;

CLOSE work_cursor;
DEALLOCATE work_cursor;
```

The real implementation must define whether any error stops the run or whether specific recoverable errors can be isolated. Do not leave that decision implicit.

The temporary error table in this sketch is session-scoped diagnostics only. If failure evidence must survive connection loss, emit an opaque run/work identifier and stable error number or class after rollback to durable telemetry. Raw engine messages can contain data values, schema details or other sensitive context; retain them only in a restricted diagnostic sink with context-aware redaction or allowlisting, access controls and bounded retention. Failure to record diagnostics must not replace the original exception, and migration completion must still be determined from target-state invariants rather than the error log.

## Plan for infrastructure failure

Before execution, decide what happens if:

- A data or log volume reaches capacity.
- The connection drops after commit acknowledgement is lost.
- The process is terminated between work items.
- An external writer modifies the same state.
- A timeout occurs while the database transaction is still active.

Restartability depends on durable target-state checks, not an in-memory progress counter.

## Verify independently

Use separate aggregate queries or constraints to verify invariants after execution:

- Eligible parents without a valid target container.
- Missing target children.
- Duplicate semantic relationships.
- Missing or conflicting required properties.
- Unresolved migration errors from durable run telemetry, where such telemetry is part of the execution design.
- Unexpected changes outside the eligible population.

A successful script exit proves that the control flow ended. It does not prove that the data reached the intended state.

## Review checklist

- Target-state invariants are explicit.
- Legacy conflicts have documented outcomes.
- Dry-run and write modes share classification logic.
- Work selection advances deterministically.
- Check-and-write is concurrency-safe.
- Transaction scope matches a recoverable business unit.
- Error policy is fail-closed by default.
- The migration can be rerun after an unknown interruption point.
- Capacity and rollback requirements are estimated.
- Independent verification queries exist before execution.

## Public references

- [SET TRANSACTION ISOLATION LEVEL](https://learn.microsoft.com/en-us/sql/t-sql/statements/set-transaction-isolation-level-transact-sql) - Microsoft Learn
- [sys.sp_getapplock](https://learn.microsoft.com/en-us/sql/relational-databases/system-stored-procedures/sp-getapplock-transact-sql) - Microsoft Learn
