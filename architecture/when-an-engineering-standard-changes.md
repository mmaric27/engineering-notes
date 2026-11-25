# When an engineering standard changes, what changes for the agent?

Revising a standard, getting that revision into an assistant’s working context and verifying the code it produces are three separate jobs. A release record tells me what was published. It does not tell me what a particular session loaded, or whether the resulting code is correct.

## 1. Revise the standard: say what to do when evidence is missing

Suppose an integration submits an order to an external system. The system commits the order, but the response never reaches the caller. Our code sees a timeout. An assistant proposes three retries with exponential backoff.

A test where the first call times out and the second succeeds passes. It tells us nothing about how many orders now exist. Backoff changes *when* we send the second request, not whether it is safe to send.

Here is the rule I would give the team and its assistants:

> Before retrying an operation with external side effects, identify the guarantee that makes it safe to repeat. If the outcome is unknown and no such guarantee is established, record it as `unknown` and reconcile before resubmitting.

For an API with a documented idempotency guarantee, generate the key **once per logical order and persist it before the first call**. A retry after a process restart must recover the same key. A fresh key on every attempt gives the receiver no reason to treat the second request as a duplicate.

Without that guarantee, keep the order in `unknown`. If the external system supports lookup by the caller’s order reference, use it to establish what happened. Resubmit only if the lookup is authoritative, finds no order, and the original request can no longer complete, for example because the receiver guarantees it will not commit the request after its documented processing deadline. A “not found” result from an eventually consistent view leaves the outcome `unknown`.

The [protocol-neutral capability design note](protocol-neutral-capability-layers-for-ai-channels.md) puts this decision in context: a timeout at the channel boundary does not establish what happened to the underlying operation.

## 2. Distribute the revision: verify what the session loaded

I want one maintained source for the rule and its rationale. The tooling can package it for different assistants without asking engineers to keep separate copies in sync.

Include the rule ID and revision in the generated skill. After publication, start a fresh session and look for a session log entry that identifies the skill loaded for the task by name and revision. Compare it with the published revision. If the host exposes only the installed version, report **installed, load unverified**. Asking the model which rule it remembers is not a substitute for that check.

## 3. Verify the result: test the decision, then test the software

**For the assistant**, use two versions of the same task. Change only the API contract. One version guarantees idempotency for a caller-supplied key; the other says nothing about duplicate requests. Write down the acceptance criteria first: reuse a persisted key in the first case; preserve `unknown` and propose reconciliation in the second. Run each variant several times in fresh sessions and record how often it meets the criteria. Retrying in both cases misses the rule. So does refusing to retry in the first case, or refusing in the second without proposing reconciliation.

**For the implementation**, make a test double record the order **and then drop the response**. Restart the caller before it can handle the timeout. On the idempotent path, verify that the next attempt uses the original key and that the receiver still holds exactly one order. On the path without that guarantee, verify that recovery preserves the uncertain outcome and initiates reconciliation without a second submission.

Inspect the receiver’s orders and the caller’s durable state, not just the return value. As the engineer, I should still be able to explain why the second request is safe, or why there isn’t one.

[Run the example: two submissions, one order; one submission, unknown outcome.](../examples/unknown-order-outcome/)
