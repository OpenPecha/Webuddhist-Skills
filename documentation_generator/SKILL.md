name: documentation
version: 2.2.0
description: "[Code Quality] Use when the user asks to enhance documentation, add code comments, create API docs, improve technical documentation, document code, or update README files. Triggers on keywords like \"document\", \"documentation\", \"README\", \"update docs\", \"improve README\", \"JSDoc\", \"XML comments\", \"API docs\"."
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, TaskCreate
---

> **[IMPORTANT]** Use `TaskCreate` to break ALL work into small tasks BEFORE starting — including tasks for each file read. This prevents context loss from long files. For simple tasks, AI MUST ask user whether to skip.

## Quick Summary

**Goal:** Enhance code documentation, API docs, README files, and technical writing with verified accuracy.

**Workflow:**

1. **Analysis** — Build knowledge model: discover APIs, components, structure, documentation gaps
2. **Plan** — Generate detailed documentation plan with priorities and outline
3. **Approval Gate** — Present plan for explicit user approval before writing
4. **Execute** — Write documentation following anti-hallucination protocols

**Key Rules:**

- Never proceed without explicit user approval of the documentation plan
- Verify every documented feature against actual code (no assumptions)
- For business feature docs, use `feature-docs` skill instead
- Include practical examples and copy-pasteable code snippets

**Be skeptical. Apply critical thinking, sequential thinking. Every claim needs traced proof, confidence percentages (Idea should be more than 80%).**

> **Skill Variant:** Use this skill for **interactive documentation tasks** including code docs AND README files.

## Disambiguation

- For **business feature docs** → use `feature-docs`
- This skill covers **code documentation** and **README files**
- For **OpenPecha org-wide README generation** → use the OpenPecha Organization Mode below

---

# OpenPecha Organization Mode

When the user asks to generate READMEs across the OpenPecha GitHub organization, follow this workflow **in full** before falling through to the standard Documentation Enhancement phases below.

**Configuration:**
- **Organization:** `OpenPecha` → `https://github.com/OpenPecha`
- **Template Source:** `https://gitlab.com/tgdp/templates/-/tree/main/readme`
- **Output Filename:** `openclaw_documentation_README.md` (never overwrite the original `README.md`)
- **Commit Message:** `docs: automated readme generation via Open Claw (TGDP Template)`
- **Auth:** Requires a GitHub PAT with `repo` and `read:org` scopes — prompt the user if not set.

---

### OPENPECHA PHASE 1: Discovery

1. Fetch all repositories from the OpenPecha GitHub organization via the GitHub API.
2. **Skip** archived repositories unless the user explicitly requests them.
3. Build a queue of active repos to process.
4. Use exponential backoff if GitHub API rate limits are hit (start at 1s, double each retry, max 5 retries).

---

### OPENPECHA PHASE 2: Per-Repo Analysis

For **each** repository in the queue, analyze:

| Signal | Source |
|---|---|
| Project name & description | GitHub repo metadata |
| Primary language & tech stack | GitHub language stats + file extensions |
| Installation steps | `requirements.txt`, `setup.py`, `pyproject.toml`, `package.json`, `Makefile` |
| Project structure | Top-level directory tree |
| Existing context | Current `README.md` and `/docs` folder (read for context only — do not copy) |

> **Anti-hallucination rule:** If the purpose of a repository cannot be confidently determined from the code and metadata, mark the Introduction section with `[Needs Manual Review]` rather than guessing.

---

### OPENPECHA PHASE 3: Generation

For each repo, generate `openclaw_documentation_README.md` using the **README Structure Template** defined below (with logo, badges, and footer already included). Map analyzed data to these sections:

- **Logo + Title + Badges** → Always use the standard header template
- **Introduction** → Concise summary of what the tool/dataset does (from metadata + code analysis)
- **Installation** → Step-by-step guide derived from detected dependency files
- **Usage** → Basic commands or API examples inferred from code (not invented)
- **Directory Structure** → Tree-view of the top-level repository layout
- **Contributing** → Standard link to OpenPecha contribution guidelines
- **How to get help + Terms of use** → Always use the standard footer template

---

### OPENPECHA PHASE 4: Deployment

For each repo:
1. Create or update `{repo_root}/openclaw_documentation_README.md`
2. **Never** touch or overwrite the original `README.md`
3. Commit with message: `docs: automated readme generation via Open Claw (TGDP Template)`
4. Report a summary of repos processed, skipped (archived), and any flagged `[Needs Manual Review]`

---

# Documentation Enhancement

You are to operate as an expert technical writer and software documentation specialist to enhance documentation.

**IMPORTANT**: Always thinks hard, plan step by step to-do list first before execute. Always remember to-do list, never compact or summary it when memory context limit reach. Always preserve and carry your to-do list through every operation.

**Prerequisites:** **⚠️ MUST READ** `.claude/skills/shared/evidence-based-reasoning-protocol.md` before executing.

---

## README Structure Template

Use this structure when creating or improving README files.

**ALWAYS start every README with the OpenPecha logo and a centered H1 title, exactly as shown below — no exceptions:**

````markdown
<h1 align="center">
  <br>
  <a href="https://buddhistai.tools/"><img src="https://raw.githubusercontent.com/WeBuddhist/visual-assets/refs/heads/main/logo/WB-logo-purple.png" alt="OpenPecha" width="150"></a>
  <br>
</h1>

<h1 align="center">Project Name</h1>

<p align="center">
  |codecov| |license|
</p>

Brief description of the project.

## Table of Contents

- [Features](#features)
- [Prerequisites](#prerequisites)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Development](#development)
- [Testing](#testing)
- [Deployment](#deployment)
- [Troubleshooting](#troubleshooting)
- [Contributing](#contributing)
- [License](#license)

## Features

- Feature 1
- Feature 2

## Prerequisites

- Node.js >= 18
- .NET 9 SDK

## Installation

```bash
# Clone the repository
git clone [url]

# Install dependencies
npm install
dotnet restore
```

## Configuration

[Configuration details]

## Usage

[Usage examples]

## Development

[Development setup]

## Testing

[Testing instructions]

## Troubleshooting

[Common issues and solutions]

## How to get help
* File an issue.
* Join our [discord](https://discord.com/invite/7GFpPFSTeA).

## Terms of use
Project Name is licensed under the [MIT License](/LICENSE.md).
````

**ALWAYS end every README with the "How to get help" and "Terms of use" sections above, replacing "Project Name" with the actual project name — no exceptions.**

---

## PHASE 1: EXTERNAL MEMORY-DRIVEN DOCUMENTATION ANALYSIS

Build a structured knowledge model in `.ai/workspace/analysis/[task-name].analysis.md`.

### PHASE 1A: INITIALIZATION AND DISCOVERY

1. **Initialize** the analysis file with standard headings
2. **Discovery searches** for all related files

### DOCUMENTATION-SPECIFIC DISCOVERY

**DOCUMENTATION_COMPLETENESS_DISCOVERY**: Focus on documentation-relevant patterns:

1. **API Documentation Analysis**: Find API endpoints and identify missing documentation. Document under `## API Documentation`.

2. **Component Documentation Analysis**: Find public classes/methods and identify complex logic needing explanation. Document under `## Component Documentation`.

3. **Basic Structure Analysis**: Find key configuration files and main application flows. Document under `## Structure Documentation`.

**PROJECT_OVERVIEW_DISCOVERY** (README-specific): Focus on README-relevant patterns:

1. **Project Structure Analysis**: Find entry points, map key directories, identify technologies
2. **Feature Discovery**: Find user-facing features and map API endpoints
3. **Setup Requirements Analysis**: Find package files, map dependencies, identify configuration needs

### PHASE 1B: SYSTEMATIC FILE ANALYSIS FOR DOCUMENTATION

> **IMPORTANT:** Must do with todo list.

For each file, document in `## Knowledge Graph`:

- Standard fields plus documentation-specific:
- `documentationGaps`: Missing or incomplete documentation
- `complexityLevel`: How difficult to understand (1-10)
- `userFacingFeatures`: Features needing user documentation
- `developerNotes`: Technical details needing developer docs
- `exampleRequirements`: Code examples or usage scenarios needed
- `apiDocumentationNeeds`: API endpoints requiring documentation
- `configurationOptions`: Configuration parameters needing explanation
- `troubleshootingAreas`: Common issues requiring troubleshooting docs

README-specific fields (when analyzing for README documentation):

| Field | Description |
| -------------------- | ------------------------------------------ |
| `readmeRelevance` | How component should be represented (1-10) |
| `userImpact` | How component affects end users |
| `setupRequirements` | Prerequisites for this component |
| `configurationNeeds` | Configuration required |
| `featureDescription` | User-facing features provided |
| `exampleUsage` | Usage examples for README |
| `projectContext` | How it fits into overall project |

### PHASE 1C: OVERALL ANALYSIS

Write comprehensive summary showing:

- Complete end-to-end workflows discovered
- Documentation gaps identified
- Priority areas for documentation
- Key features and capabilities (README)
- Setup and configuration requirements (README)

---

## PHASE 2: DOCUMENTATION PLAN GENERATION

Generate detailed documentation plan under `## Documentation Plan`:

- Focus on completeness
- Ensure clarity
- Include examples
- Maintain consistency

For README plans, generate a detailed outline covering: Project Overview, Installation, Usage, Configuration, Development guidelines.

---

## PHASE 3: APPROVAL GATE

**CRITICAL**: Present documentation plan for explicit approval. **DO NOT** proceed without it.

---

## PHASE 4: DOCUMENTATION EXECUTION

Once approved, execute the plan using all DOCUMENTATION_SAFEGUARDS.

---

## SUCCESS VALIDATION

Verify documentation is:

- Accurate (matches actual code)
- Complete (covers all public APIs)
- Helpful (includes examples)

README-specific checks:

- [ ] **Accurate**: All instructions work
- [ ] **Comprehensive**: Covers all setup needs
- [ ] **Helpful**: New users can get started
- [ ] **Tested**: Commands verified to work

Document under `## Documentation Validation`.

---

## Documentation Guidelines

- **Accuracy-first approach**: Verify every documented feature with actual code
- **User-focused content**: Organize documentation based on user needs
- **Example-driven documentation**: Include practical examples and usage scenarios
- **Consistency maintenance**: Follow established documentation patterns
- **No assumptions**: Always verify behavior before documenting

### README Guidelines

- **User-first approach**: Organize content for new users; start with what the project does and why; provide clear getting-started path
- **Verified instructions**: Test all setup and installation instructions; include exact commands that work; document version requirements
- **Practical examples**: Include working examples users can follow; show common use cases; provide copy-pasteable code snippets
- **No assumptions**: Don't assume user knowledge; explain acronyms and domain terms; link to prerequisite documentation

**⚠️ MUST READ:** CLAUDE.md for code pattern examples (backend/frontend) when writing code documentation. See `.claude/docs/` for existing documentation structure.

---

## Anti-Hallucination Protocols

### ASSUMPTION_VALIDATION_CHECKPOINT

Before every major operation:

1. "What assumptions am I making about [X]?"
2. "Have I verified this with actual code evidence?"

### EVIDENCE_CHAIN_VALIDATION

Before claiming any relationship:

- "I believe X calls Y because..." → show actual code
- "This follows pattern Z because..." → cite specific examples

### TOOL_EFFICIENCY_PROTOCOL

- Batch multiple Grep searches into single calls with OR patterns
- Use parallel Read operations for related files

### CONTEXT_ANCHOR_SYSTEM

Every 10 operations:

1. Re-read the original task description
2. Verify the current operation aligns with original goals

---

## Related

- `feature-docs`
- `changelog`
- `release-notes`

---

### Task Planning Notes (MUST FOLLOW)

- Always plan and break work into many small todo tasks
- Always add a final review todo task to verify work quality and identify fixes/enhancements
