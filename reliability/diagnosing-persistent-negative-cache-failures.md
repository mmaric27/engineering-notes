# Diagnosing Persistent Failures Caused by Negative Caching

> This note uses a synthetic composite assembled from common distributed-systems and HTTP caching failure modes. It is not an account of a particular employer, client, system or production incident.

## The failure pattern

In a generic distributed application, a dependency failure can be misclassified as resource absence. If that result is negatively cached, clients may continue to receive an incorrect not-found response after the dependency recovers.

Possible indicators include:

- Different nodes return inconsistent results for equivalent request context.
- Incorrect not-found responses persist beyond dependency recovery.
- Bounded cache invalidation clears the incorrect state.
- Request-failure volume is not explained by application exception volume.

## Distinguish three states

The application must not collapse these states into one value:

```text
Confirmed present
Confirmed absent
Could not determine because generation or dependency access failed
```

Only authoritative absence evaluated with the complete request context is a candidate for negative caching. Operational failure must not be stored as absence. Retry, backoff and circuit-breaker state must remain distinct from the cached domain result.

## Build an evidence timeline

Normalize timestamps and correlate independent evidence categories:

- Request telemetry by node, route template, opaque or privacy-preserving key identifier, status and latency.
- Application lifecycle events and restart reasons.
- Application error and structured diagnostic logs.
- Dependency latency, timeout and saturation signals.
- Cache hit/miss or invalidation telemetry where available.
- External availability and user-impact measurements.

Prefer a server-generated opaque identifier and log only the non-sensitive state needed for diagnosis. If separate events must be correlated by cache key, use a scoped, keyed HMAC rather than logging the raw key. Protect the HMAC key, restrict access to the telemetry and limit retention. Treat derived identifiers as potentially pseudonymous, not anonymous.

Record missing telemetry explicitly. Missing evidence reduces confidence; it does not prove that an event did not occur.

## Establish baseline and episode boundaries

Group requests by time window and node to determine:

- Normal negative-response rate.
- Episode start and end.
- Whether failures are node-local or shared.
- Whether the same key alternates between success and failure.
- Whether failures persist after dependency latency returns to normal.

A node-local pattern narrows the investigation toward node-specific state, configuration, routing or dependency reachability. A simultaneous cross-node pattern points toward a shared dependency, coordinated deployment, shared cache or common input.

## Form a testable cause chain

A generic chain to test is:

1. A dependency call fails.
2. The application incorrectly classifies that failure as authoritative absence.
3. The negative result is inserted into a cache.
4. Stale not-found responses continue after dependency recovery.

Treat the chain as a hypothesis until every link has evidence. Static source inspection can establish that the proposed mechanism exists, but it cannot show that the path executed during an incident. Runtime traces or state-transition telemetry can show actual execution. A controlled reproduction can demonstrate that the mechanism is possible under known conditions, but it does not prove that the same path executed during a historical incident. Record the evidence basis and confidence separately for each link.

## Test competing hypotheses

For each hypothesis, define evidence that supports it and evidence that weakens it:

| Hypothesis | Evidence that supports it | Evidence that weakens it |
| --- | --- | --- |
| Resource is genuinely absent | The authoritative source reports absence for the complete request context | The authoritative source reports presence and an uncached lookup succeeds |
| The application process terminated | Lifecycle telemetry records termination and a process or instance identity change | Process identity and uptime remain continuous across the episode |
| A deployment introduced the issue | Onset aligns with rollout and failures segment by build or configuration version | The same version operates normally before and after onset with no relevant configuration change |
| An edge cache generated or retained the response | Edge and origin responses differ, or cache headers show edge retention | Correlated origin telemetry records the same response |
| Origin-to-dependency communication failed | Dependency-call telemetry records aligned connection or timeout failures | Successful calls from the same node and interval contradict the proposed network scope |
| Workload pressure triggered the episode | Concurrency, request mix, initialization work or dependency demand rises at onset | Those demand measures remain within the established baseline |
| Node-local state retained the failure | Failures remain tied to one process and clear after targeted invalidation or process replacement | The failure follows the complete request context consistently across independent nodes |

Do not reject a hypothesis because expected telemetry is missing. Record the test as inconclusive.

## Common contributing conditions

- Dependency performance degradation during initialization or burst load.
- No retained history for comparing normal and degraded behavior.
- Shared dependencies with insufficient workload isolation.
- Negative caching without an appropriate TTL or complete cache key.
- Broad invalidation that hides the affected state instead of identifying it.
- Logging that records exceptions but not incorrect state transitions.
- Monitoring that checks only a small route sample.

These conditions may increase probability or impact without being the root defect.

## Remediation priorities

1. Do not translate an operational timeout or generation failure into a cacheable `404`.
2. Model authoritative absence separately from generation failure.
3. Give confirmed-absence entries an explicit TTL and invalidation path appropriate to the source's consistency model.
4. Log the transition with an opaque correlation identifier, node identity and failure class. Do not log cache values, credentials, personal data or raw user-supplied keys.
5. Retain the request, application and dependency evidence needed to test causal links.
6. Prefer targeted invalidation over broad process replacement.
7. Define a primary user-impact indicator and retain the telemetry needed to explain it.
8. Alert on route-level failure ratios, not only unhandled exceptions.

## Validation strategy

After remediation, test that:

- A dependency timeout produces a failure response, not confirmed absence.
- A transient operational failure is not stored as a negative cache entry; any retry or backoff state expires independently.
- Recovery occurs without restarting the process.
- Nodes converge to the same state.
- Dashboards expose both the primary failure metric and supporting evidence.

## Review checklist

- Presence, absence and operational failure are distinct states.
- Negative cache entries have bounded lifetime and explicit invalidation.
- Cache keys include every input that can change the result, such as tenant, locale, authorization scope, route variant and content version where applicable.
- Relevant cache events can be correlated without logging raw cache keys, cached values or sensitive data.
- Node-local and shared-state behavior can be distinguished.
- Each causal link records its evidence basis, such as observed telemetry, static code inspection or controlled reproduction, and a separate confidence rating.
- Remediation success has measurable acceptance criteria.

## Public references

- [RFC 9111: HTTP Caching](https://www.rfc-editor.org/rfc/rfc9111) - IETF
