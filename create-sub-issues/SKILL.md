---
name: project-board-to-tasks
description: General-purpose agent to ANY GitHub Project, pick a project board, break down tasks
---

## Inputs (User-Defined)

- PROJECT_URL: "The URL of the GitHub Project Board"
- TARGET_REPO: "The 'org/repo' where issues should be created"
- TARGET_VIEW: "e.g., 'Sprint 7', 'Backlog', or 'To Do'"
- PRIORITY_LABEL: "The label or status to prioritize (e.g., 'High', 'Bug', 'To Do')"
- BRANCH_PREFIX: "Prefix for git branches (default: feature/)"

## Safety Guardrails (Global)

- **Constraint**: Never execute `DELETE` or `CLOSE` on any existing issues.
- **Constraint**: If no task is found matching `PRIORITY_LABEL`, STOP and report "Target Priority Not Found".
- **Constraint**: Max 5 sub-tasks allowed per parent issue to prevent API spiraling.

## Step 1: Secure Scout & Analyze

1. **Fetch**: Access `PROJECT_URL` and filter by `TARGET_VIEW`.
2. **Scan**: Identify the top item matching `PRIORITY_LABEL`.
3. **Validation**: Check if the item is already "In Progress". If YES, skip to next.
4. **Draft**: Analyze `body` and `title`. Generate sub-tasks including:
   - **Title**: Prefixed with `[Sub-task]`.
   - **Technical Description**: 2-sentence summary of implementation.

## Step 2: Strategic Human Oversight

1. **Report**: Present the "Proposed Execution Plan":
   - **Source Task**: [Title]
   - **Target Repo**: `TARGET_REPO`
   - **Sub-tasks**: [List generated in Step 1]
2. **Mandatory Pause**: Trigger `HUMAN_INTERVENTION`.
   - **Instruction**: Wait for user to type `APPROVE` or `CANCEL`.
