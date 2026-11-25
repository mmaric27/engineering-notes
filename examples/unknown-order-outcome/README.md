# Unknown order outcome

This fictional example shows what happens when a receiver records an order but its response never reaches the caller.

From this directory, run `python -m unittest -v`. Only the Python standard library is required.

Tested with Python 3.15.0 and SQLite 3.53.1. The receiver uses SQLite UPSERT syntax (`ON CONFLICT ... DO NOTHING`), which requires SQLite 3.24.0 or later.

- **With an idempotency guarantee:** after restart, the caller recovers the original key. The receiver sees two submissions but stores exactly one order.
- **Without an idempotency guarantee:** after restart, the caller reconciles using the original order reference rather than submitting again. A non-authoritative “not found” leaves the outcome `unknown`.

Each test starts two caller processes with `sys.executable`. The receiver is a test double, not an HTTP service. It commits to its own SQLite database before simulating a lost response; the caller recovers from a separate database. Both files live in a temporary directory. The example does not model processing deadlines or authorize resubmission after a negative lookup.
