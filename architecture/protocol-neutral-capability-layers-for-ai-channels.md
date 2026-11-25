# Protocol-neutral capability layers for AI channels

**Source review date:** 2026-11-04

An AI channel should provide another way to use an application's capabilities, not another place to implement its business rules.

This note applies ports-and-adapters reasoning to browser-facing tools and MCP integrations. It uses a fictional repair-workshop application. It is not a case study of an employer or client system, and it does not claim a tested implementation or production results.

## 1. Start with the use case, not the protocol

Suppose a repair workshop wants customers to explore service options and request work through either its website or an assistant.

The application already needs to answer three different questions:

- Which services are available for this type of equipment?
- What would a proposed work order contain?
- Is this caller allowed to create that work order now?

These are application concerns. They should not acquire different answers merely because one request arrived through a web interface and another through an MCP tool.

Ports-and-adapters architecture separates purposeful application interfaces from the technologies used to invoke them [1]. An AI integration can use that existing pattern without inventing a new business layer for every assistant.

## 2. Browser tools and MCP servers are different integration surfaces

The reviewed WebMCP draft describes a JavaScript interface through which web applications expose tools to agents. Its model includes document context and browser security considerations [2].

MCP defines a host-client-server architecture. Servers can run locally or remotely and expose tools, resources and prompts [3]. A remote MCP server is one deployment choice, not the definition of every MCP integration.

| Question | Browser-facing WebMCP integration | Remote MCP server integration |
| --- | --- | --- |
| Where is the tool implemented? | In web application JavaScript | In a server reached by an MCP client |
| What context needs examination? | Document lifecycle, browser support and the application's session | Client support, protocol capabilities, server authorization and backend access |
| What must be verified? | The exact browser-agent combination and required API behavior | The exact host-client-server combination and required features |
| What does its existence not prove? | Availability to every assistant or operation without the page | Access to the user's browser session or permission to act on every backend resource |

As reviewed on 2026-11-04, WebMCP is a Draft Community Group Report, not a W3C Standard. This note does not establish browser availability or cross-product interoperability.

The MCP references here use specification version 2025-11-25. That is a stated reference baseline, not a claim that it is the latest version.

Neither integration surface makes application authorization, transaction safety or business validation optional.

## 3. Define a small application capability boundary

For the fictional workshop, an initial boundary might contain:

| Capability | Purpose | Side effect |
| --- | --- | --- |
| `listServiceOptions` | Return options applicable to an equipment category | Read only |
| `previewWorkOrder` | Validate a proposed request and return its current terms | No work order created |
| `createWorkOrder` | Create an authorized request after required confirmation | Durable write |

These are illustrative application operations, not standard MCP or WebMCP methods.

A possible arrangement is:

```text
Browser UI or WebMCP tool
    -> authenticated application API --------+
                                             |
Remote assistant -> MCP server adapter ------+
                                             |
                                             v
                           Application capability boundary
                           - resource authorization
                           - input and business validation
                           - confirmation verification
                           - concurrency and idempotency
                                             |
                                             v
                              Existing domain services
                                             |
                                             v
                              Authoritative work-order store
```

Authentication and transport-specific protections also apply at each entry point. The diagram does not imply that a browser may call private application code directly or that an MCP server may bypass the application's API security.

The shared boundary can be a module inside an existing application. It does not require another deployable service, a universal tool gateway or a rewrite.

## 4. Keep adapters thin, but do not make them blind

An adapter translates its channel's contract into an application operation.

Its responsibilities can include:

- Validating the transport envelope and mapping arguments.
- Establishing a verified caller context.
- Enforcing channel-specific restrictions.
- Mapping domain errors into the channel's error format.
- Applying timeouts, response limits and correlation identifiers.

The application remains responsible for resource-level authorization, business invariants and durable state changes.

Do not accept caller identity, tenant membership or approval as authoritative merely because the model supplied them as arguments. Derive or verify them through trusted authentication and authorization mechanisms.

MCP defines tool schemas and execution-error handling, but those structures do not replace domain validation [4]. Its HTTP authorization specification addresses access to the MCP server; downstream application access still needs an explicit design [5].

Protocol-neutral does not mean security-neutral. Different adapters may expose different subsets of the same application capabilities.

## 5. Separate discovery, preview and commitment

A tool that lists services should not silently create a work order.

A preview should make the proposed operation understandable without committing it. For a consequential write, bind confirmation to the relevant operation and parameters. Recheck authorization and mutable business conditions when committing.

For example:

1. The caller requests a preview.
2. The application returns the normalized request, applicable terms and a validity boundary.
3. The user reviews the proposed action.
4. The application verifies the confirmation and current conditions before creating the order.

A conversational "yes" is not sufficient evidence if the operation or its parameters have changed.

Idempotency is a separate concern from confirmation. A write contract should define:

- The scope and retention of an idempotency key.
- How the key is bound to the caller and request payload.
- What happens if the same key arrives with different parameters.
- How concurrent duplicates are handled.
- How the caller checks the outcome after a timeout.

A timeout or cancellation does not prove that a durable operation was rolled back. Do not automatically retry an ambiguous write with a new key.

For a [worked example of an order with an unknown outcome](when-an-engineering-standard-changes.md), see how the retry decision changes with the receiver’s contract. The [runnable tests](../examples/unknown-order-outcome/) check the receiver’s stored orders after the caller restarts.

## 6. Keep authority outside generated text

A model-generated explanation is not the work-order record.

Return structured results that distinguish:

- Validated data from explanatory text.
- A preview from a committed operation.
- A confirmed failure from an unknown outcome.
- Current information from cached or expired information.

For time-sensitive results, include useful freshness or validity metadata. Revalidate at commitment rather than treating an earlier response as a reservation.

Treat tool descriptions, external documents and free-text result fields as potential prompt-injection surfaces. OWASP recommends layered controls and explicitly warns that prompt wording and input screening are not enforcement boundaries [6].

Practical controls include:

- Narrow operation and resource permissions.
- Server-side argument and authorization checks.
- Minimal data returned to the model.
- Explicit confirmation for consequential actions.
- Limits on calls, output size, duration and retries.
- Audit records that avoid credentials and unnecessary personal data.

MCP tool annotations are not a substitute for enforcement; the reviewed specification requires clients to treat annotations as untrusted unless they come from trusted servers [4].

## 7. Verify behavior before expanding the integration

Start with one bounded use case and a documented target environment. Record which browser, agent, MCP host and protocol versions are actually tested.

A useful test plan includes:

| Scenario | Expected property |
| --- | --- |
| Equivalent requests through two adapters | Same domain result for equivalent authorized context |
| Unauthorized resource identifier | Rejected regardless of channel |
| Invalid or extra arguments | Rejected or handled according to the explicit contract |
| Expired preview | Revalidation or a new preview before commitment |
| Duplicate write | No duplicate effect within the documented idempotency contract |
| Same key with changed payload | Explicit conflict |
| Timeout after submission | Outcome reconciliation rather than an assumed failure |
| Malicious text in a tool result | No expansion of permissions or unauthorized side effect |
| Unsupported browser or client | Clear limitation and an available non-AI path |

These are proposed checks, not test results from an implementation.

For a feasibility exercise, agree acceptance thresholds before testing. Measure successful task completion, incorrect or unauthorized actions, latency, cost per completed task and recovery from failure. Include ordinary user requests as well as adversarial cases.

A successful demonstration establishes only what was tested. It does not establish production readiness or business value.

## 8. Choose the smallest useful design

| Option | Appropriate when | Main trade-off |
| --- | --- | --- |
| Existing API with one thin adapter | One concrete channel and mature application capabilities | Lowest initial complexity; avoid leaking channel assumptions into business code |
| Shared application boundary with multiple adapters | Several justified channels need consistent behavior | Additional contract and compatibility testing |
| Managed connector or integration product | Its permissions, lifecycle and capabilities fit the use case | Less adapter maintenance, but product constraints and dependency risk |

Do not build a generic platform solely because more channels might appear later.

A managed connector does not remove the need to verify authorization, data handling, retries, observability and exit options. A custom adapter does not automatically provide those controls either.

## Conclusion

Keep business capabilities stable and make channel integrations replaceable.

The useful architectural boundary is not "AI versus non-AI." It is the boundary between an untrusted request and an authorized application operation with explicit semantics, observable outcomes and tested failure behavior.

## Sources

Public sources reviewed on 2026-11-04. Recommendations and the fictional example are this note's synthesis, not requirements attributed wholesale to a protocol.

1. [Alistair Cockburn: Hexagonal architecture](https://alistair.cockburn.us/hexagonal-architecture) - Application boundaries, ports and adapters.
2. [WebMCP Draft Community Group Report](https://webmachinelearning.github.io/webmcp/) - Browser-facing tool model and draft status; reviewed document dated 2026-11-02.
3. [MCP architecture, version 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/architecture) - Hosts, clients and local or remote servers.
4. [MCP tools, version 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools) - Schemas, results, errors and security considerations.
5. [MCP authorization, version 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/basic/authorization) - HTTP transport authorization and token audience boundaries.
6. [OWASP LLM Prompt Injection Prevention Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/LLM_Prompt_Injection_Prevention_Cheat_Sheet.html) - Defense in depth, least privilege and tool-boundary enforcement.
