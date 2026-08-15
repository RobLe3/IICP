# Public artifact and private-method boundary

## Purpose

IICP's public repositories must be sufficient to review, implement, test and
maintain the protocol. They do not need to disclose the private development
system that produced the work.

This boundary applies to specification releases, standards-review material,
public research, implementation repositories and conformance evidence.

## Public artifacts

The public record includes:

- normative specifications, registries, schemas and compatibility rules;
- source code for public implementations;
- technical research that affected a feature or protocol decision;
- experimental methods, inputs and limitations needed to reproduce a result;
- alternatives considered, rejected approaches and compatibility consequences;
- public architecture and security decisions;
- milestone definitions expressed as observable acceptance criteria;
- conformance fixtures, tests and content-free evidence;
- release, build, maintenance and contribution instructions.

A future implementer should be able to determine what was decided, which
evidence supported it, what remains uncertain and what would justify revisiting
the decision.

## Private material

Private material includes development-loop implementation, agent prompts,
orchestration, internal work selection, personal reasoning systems, private
meta-tools, credentials, private topology and operational history. Public
builds and protocol decisions must not depend on that material.

Private tools may check public artifacts, but their names, scores or internal
state are not public acceptance evidence. The public evidence must be
reproducible with the commands and inputs shipped in the public repository.

## Mixed-source treatment

When private work produces a public product decision, publish a self-contained
record containing the question, evidence, alternatives, decision,
consequences, limitations and acceptance criteria. Do not publish the private
workflow that generated or prioritized the work.

When a public artifact refers to private material, use one of these treatments:

1. state the required technical rule in the public specification;
2. create a sanitized public decision or research record;
3. cite public fixture, test or release evidence; or
4. remove the reference when it is historical and unnecessary.

Public issue summaries must not copy private comments, credentials, personal
data or operational details.

## Closure rule

A normative or review-facing artifact is self-contained only when every local
reference resolves within the public repository or release and every external
reference is publicly retrievable. A private repository, internal project path
or workstation-local path cannot be normative authority.

The public-artifact closure checker enforces this mechanical boundary. Human
review remains responsible for deciding whether the published rationale and
evidence are sufficient.
