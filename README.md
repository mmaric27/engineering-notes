# Engineering Notes

Practical notes on SQL migration safety, reliability diagnostics and legacy modernization.

These notes explain general engineering patterns. Examples use synthetic names and newly written pseudocode and are not presented as accounts of any particular employer, client, project, system or incident. No third-party source code, documentation, identifiers, infrastructure values or non-public measurements are intentionally included.

## Notes

| Area | Note | Focus |
| --- | --- | --- |
| SQL and data | [Designing restartable data migrations](sql/designing-restartable-data-migrations.md) | Convergent state, concurrency, transactions, restartability and verification |
| Reliability | [Diagnosing persistent failures caused by negative caching](reliability/diagnosing-persistent-negative-cache-failures.md) | Evidence correlation, causal confidence and safe negative caching |
| Modernization | [Planning a safe TFVC-to-Git migration](modernization/planning-tfvc-to-git-migration.md) | History conversion, sensitive-data controls, freeze, cutover and audit linkage |

## Working Principles

1. Measure the current state before changing it.
2. Separate symptoms, contributing conditions and root causes.
3. Make unknowns and missing evidence explicit.
4. Design changes to be observable and recoverable, with explicit rollback or resume behavior where applicable.
5. Verify outcomes independently of the implementation path.
6. Keep modernization steps small enough to review and either reverse or recover from.

## About

Written by [Marko Marić](https://www.linkedin.com/in/mark-om42), Senior Software Engineer and hands-on Solution Architect focused on SQL, backend and data systems, integrations, legacy modernization and production root-cause analysis.

Generative AI assisted with outlining and copy-editing. The author selected the topics, reviewed the technical content and approved the published wording. This statement records editorial review only and does not claim ownership of, or permission to publish, any third-party material.

## License

Licensed under [Creative Commons Attribution 4.0 International](LICENSE).
