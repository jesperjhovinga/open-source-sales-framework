# Architecture language

Shared vocabulary for every suggestion this skill makes. Use these terms exactly — don't substitute "component," "service," "API," or "boundary." Consistent language is the whole point. Adapted from mattpocock/skills `improve-codebase-architecture` LANGUAGE.md for a markdown skill/spec/context framework instead of a codebase.

## The mapping (code-world → this framework)

| Original (code) | Here (BD framework) |
|---|---|
| Module = function/class/package | **Module** = a skill, a context surface, or a spec |
| Interface = type signature + invariants | **Interface** = a skill's `description`/trigger + expected inputs; a surface's contract signature |
| Implementation = code body | **Implementation** = the SKILL.md body / context file content / spec process |
| Seam = where behaviour can be swapped | **Seam** = the context contract (swap the Org Context → new company) |
| Adapter = concrete impl at a seam | **Adapter** = an Org Context instance (`contexts/<org>/`) |
| Test surface | **Trigger surface** (how/when the skill activates) |

## Terms

**Module** — anything with an interface and an implementation. Scale-agnostic: a single skill, a context surface, or a whole spec. _Avoid_: component, unit, service.

**Interface** — everything a caller (the agent, at trigger time) must know to use the module correctly. For a skill: its description, when it fires, what inputs it needs, what it returns. Not just the one-line summary. _Avoid_: API, signature (too narrow).

**Implementation** — what's inside the module: the body of the SKILL.md, the prose of a context file, the steps of a spec.

**Depth** — leverage at the interface: how much BD capability a single invocation gets per unit of interface the agent has to learn. **Deep** = a lot of behaviour behind a small, clear trigger. **Shallow** = the description is nearly as complex as the body, or the skill mostly forwards to others.

**Seam** _(from Michael Feathers)_ — a place where behaviour can be altered without editing in that place. This framework's defining seam is the **context contract**: Core reads surfaces, Org Context supplies them. Choosing what is a surface (vs. baked into a skill) is the central design decision. _Avoid_: boundary (overloaded with DDD's bounded context).

**Adapter** — a concrete thing satisfying a surface at the seam. `contexts/<org>/` is the ExampleOrg adapter. A `contexts/_template/` would be the blank adapter that proves the seam is real.

**Leverage** — what invocations gain from depth: more BD capability per unit of interface learned. One context surface pays back across every skill that reads it.

**Locality** — what maintainers gain from depth: a change (e.g. the tone of voice) lives in one place and fixes every skill at once, instead of being duplicated across many.

## Principles

- **Depth is a property of the interface, not the implementation.** A deep skill can internally reference several context surfaces — they just aren't part of its trigger.
- **The interface is the trigger surface.** If two skills fire on the same intent, their interfaces overlap — shallowness at the seam, and a source of mis-triggers.
- **The deletion test.** Delete the module: if complexity vanishes, it was a pass-through; if complexity reappears across callers/invocations, it was earning its keep.
- **One adapter = hypothetical seam. Two adapters = real seam.** Don't claim a seam is real (portable) until something actually varies across it. One Org Context proves nothing; a second (or a template) does.

## Rejected framings

- **Depth as implementation-lines ÷ interface-lines** — rewards padding. Use depth-as-leverage.
- **"Interface" as just the one-line description** — too narrow; interface = every fact the agent needs to invoke correctly.
- **"Boundary"** — overloaded with DDD. Say **seam** or **interface**.
