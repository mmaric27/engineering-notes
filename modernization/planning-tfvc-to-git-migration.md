# Planning a Safe TFVC-to-Git Migration

> This is general technical guidance using synthetic examples and public references. It is not an account of a particular employer, client, project or completed repository migration.

Decide which TFVC history you need, then use a trial import to check that each Git branch tip matches its source changeset before cleanup. At cutover, freeze TFVC, verify the final branch contents and scan the history you intend to publish before pushing it. Open Git to normal writes only after its permissions, branch policies and build validation pass their acceptance checks.

## Migration is more than copying files

A TFVC-to-Git migration changes history representation, branching, contributor identity, permissions and the delivery workflow. Copying the latest source tree into a new repository may be sufficient for disposable code, but it is not enough when history, auditability or active branches matter.

The planned workflow may depend on Git-native pull requests, branch policies and CI/CD integration that the existing TFVC setup does not provide. Those workflow goals should be explicit; TFVC itself does not inherently prevent build pipelines or cloud migration.

## Decide what history is worth preserving

Inventory:

- TFVC root and branch paths.
- Relevant changeset ranges.
- Branch relationships and deployed state.
- Contributors and service identities.
- Shelvesets and pending changes.
- Large generated dependencies.
- Legacy source-control binding files.
- Sensitive configuration, signing material and binary secrets.
- TFVC labels and whether they represent reproducible repository snapshots.
- Merge relationships, including partial merges.
- Check-in notes and work-item associations.
- Path-level permissions and inherited access rules.
- Check-in policies, gated builds, build definitions and service hooks.

Choose deliberately between:

- Tip-only migration.
- Limited history for a defined period.
- Full useful changeset history.

More history can preserve additional audit evidence, but it also increases migration and disclosure risk. Import only the history with a documented use.

## Run a trial import

Use a tool and mode that support the required branch and history model. Record the exact tool version and options because branch behavior can vary.

A trial import should verify:

- Expected TFVC changesets are represented as traceable Git commits.
- Relevant branches exist and point to expected states.
- Contributor identities are mapped intentionally.
- Converted commits retain the source TFVC changeset identifier or an equivalent audit mapping.
- Representative historical changes are readable.
- Branch-tip trees match their corresponding final TFVC changesets before cleanup.

Document what the selected tool preserves, synthesizes or omits. TFVC labels, partial merges and path-level history might not have exact Git equivalents. Preserve an explicit mapping or retain the read-only TFVC source when Git cannot represent the original evidence faithfully.

Treat the first successful conversion as evidence, not as the cutover.

## Protect sensitive history

`.gitignore` reduces accidental addition of untracked files. It does not block forced additions, untrack an existing file or remove content from Git history.

Before any destination push, scan every object reachable from the refs intended for publication, including branches, tags, large files and relevant binary formats. Automated scanning is a detection control, not proof that no sensitive data exists.

Review for:

- Credentials, tokens and secret-bearing connection strings.
- Private keys, signing keys and certificate bundles containing private keys.
- Sensitive configuration and secrets embedded in binary files.
- Personal identity data whose publication is not justified.

If a credential or private key is found, revoke or rotate it immediately, regardless of whether the affected history will be published. Do not push an affected ref until the history has been rewritten or the ref has been excluded. After remediation, scan the exact publication refs again.

Quarantining an old repository can be a retention decision, but it does not remediate an exposed credential. Do not describe a repository as verified merely because sensitive files are absent from the latest tree or because one scanner reports no findings.

## Map contributor identity

Create an explicit author map from TFVC identities to intended Git authors. Decide how to handle:

- Renamed or disabled accounts.
- Service identities.
- Shared legacy accounts.
- Contributors without a suitable public e-mail.
- Unmapped historical changesets.

Preserving attribution is useful only when the mapping is accurate and does not expose personal data contrary to the destination's visibility.

Imported Git author fields are attribution metadata derived from the mapping. They are not authentication, a commit signature or proof that the mapped person created a Git commit. Retain the author-map version and source changeset mapping as audit evidence.

## Keep cleanup separate

First prove that each imported branch tip matches its final TFVC changeset. Then record intentional cleanup in a separate, reviewable Git commit.

Typical cleanup includes:

- Legacy source-control binding files.
- Committed package caches.
- IDE state and local paths.
- Build output.
- Obsolete generated files.
- Ignore rules, secret-manager references and push-time controls for local secrets and signing material.

Do not combine application refactoring with source-control conversion. Independent changes make source comparison and rollback much easier.

## Cut over without a write race

After the trial import is accepted:

1. Reconcile or explicitly disposition pending changes and shelvesets before the freeze.
2. Announce the freeze window, migration owner and rollback authority.
3. Deny TFVC check-in to every identity except a dedicated migration identity, and test the effective permission.
4. Restrict destination writes to the migration identity until acceptance is complete. Disable or isolate pipelines, service hooks and deployment triggers during import.
5. Import the final changesets for every in-scope branch.
6. Record the final TFVC changeset represented by each Git branch.
7. Complete the sensitive-data scan and final tree comparison for the exact refs intended for publication.
8. Push only those verified refs to the destination.
9. Configure and test repository permissions, branch policies, default branch, build validation and service identities.
10. Run the acceptance checks, declare Git authoritative and only then enable normal Git writes.
11. Leave the original TFVC paths unchanged where practical, make them read-only and record their archival status.
12. Update the application inventory and operational documentation.

The freeze is effective only when source and destination permissions have been tested. Any emergency TFVC write invalidates the recorded final changeset and requires the final import and verification to be repeated.

## Define archival controls

Read-only status is not enough by itself. Define:

- Named owner.
- Least-privilege read access.
- Audit logging where available.
- Retention purpose and review date.
- Recovery procedure.
- Conditions for eventual deletion.

The goal is audit continuity without turning the legacy source into an unmanaged permanent copy.

## Verify the destination

Verification should cover:

- Expected changeset-to-commit count or documented exceptions.
- Expected branch count and branch-tip mapping.
- Contributor identity mapping and unresolved identities.
- Full-history sensitive-data scan result.
- Pre-cleanup tree comparison for each branch.
- Intentional cleanup isolated in a reviewed commit.
- Branch policies and repository permissions.
- CI validation appropriate to the application's current state.
- TFVC write protection.
- Updated inventory and handover documentation.

## Rollback and recovery

Define rollback before the freeze:

- Conditions that invalidate the Git destination.
- Who can temporarily restore TFVC write access.
- How changes made during a failed cutover are reconciled.
- How the next migration attempt starts from a known changeset.

Avoid automatic fallback in which both repositories become writable. Recovery should restore one authoritative source.

## Review checklist

- History scope has a documented reason.
- Branch and changeset inventory is complete.
- Trial import tool, version and options are recorded.
- Author mapping is reviewed.
- Every imported ref is scanned for sensitive history.
- Branch tips match final TFVC changesets before cleanup.
- Cleanup is a separate Git commit.
- TFVC is frozen before the final import.
- Destination policies and permissions are verified.
- Archival access has owner, purpose and review date.
- Rollback restores one authoritative source.

## Public references

- [Import and migrate repositories from TFVC to Git](https://learn.microsoft.com/en-us/azure/devops/repos/git/import-from-tfvc) - Microsoft Learn
- [Removing sensitive data from a repository](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/removing-sensitive-data-from-a-repository) - GitHub Docs
