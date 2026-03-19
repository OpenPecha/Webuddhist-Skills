---
name: alternative-suggestions
description: Surfaces and compares alternative ways to implement the same thing (patterns, libraries, APIs, syntax). Use when the user or codebase would benefit from seeing options and trade-offs before choosing an approach.
---

# Alternative Suggestions Skill

## Overview

This skill guides how to identify, present, and compare **alternative ways of doing the same thing** in code. It applies when a task can be solved in more than one way—different patterns, libraries, APIs, or syntax—and the goal is to help the user or team make an informed choice rather than picking a single approach by default.

## When to Use

- User asks for "different ways to…", "alternatives to…", or "should I use X or Y?"
- Implementing a feature where multiple patterns or libraries are valid (e.g. state management, form handling, data fetching).
- Refactoring or adding code and the codebase could adopt a different convention or dependency.
- Reviewing existing code and suggesting cleaner or more consistent alternatives that fit the project.

## Core Capabilities

- **Identify alternatives**: Same outcome via different patterns (e.g. controlled vs uncontrolled form), libraries (e.g. React Hook Form vs Formik), or APIs (e.g. `fetch` vs axios, REST vs GraphQL client).
- **Compare trade-offs**: Performance, bundle size, learning curve, consistency with the rest of the codebase, maintainability, and project conventions.
- **Present clearly**: List options with pros/cons and a short recommendation when one option is clearly better for this project.

## Categories of Alternatives

| Category | Examples |
|----------|----------|
| **Patterns** | Controlled vs uncontrolled components, composition vs inheritance, server components vs client + fetch |
| **Libraries** | React Hook Form vs Formik, TanStack Query vs SWR, Zod vs Yup |
| **APIs / clients** | `fetch` vs axios, Supabase client vs Genql, REST vs GraphQL |
| **Syntax / style** | `function` vs arrow functions, `interface` vs `type`, optional chaining vs manual checks |
| **Architecture** | MVC layers, feature-based vs layer-based folders, server actions vs API routes |

## Guidelines

1. **Respect project rules**: Prefer options that align with the project’s existing stack and conventions (e.g. user rules: Next.js App Router, Supabase, Shadcn, Zod, `function` keyword, RORO).
2. **Keep the list focused**: Usually 2–4 alternatives; avoid overwhelming with every possible option.
3. **State trade-offs explicitly**: For each alternative, briefly note pros and cons (e.g. "less boilerplate but less type safety").
4. **Recommend when clear**: If one option is clearly better for this codebase, say so and why; otherwise present options and let the user decide.
5. **Minimal change first**: If the user didn’t ask for alternatives, don’t refactor by default—only suggest alternatives when it’s relevant or when they ask.

## How to Present Alternatives

Use a consistent structure:

1. **Context**: What we’re solving (e.g. "Form validation for the annotation form").
2. **Options**: Short name and one-line description per option.
3. **Comparison**: A small table or bullet list of trade-offs (bundle size, DX, consistency, etc.).
4. **Recommendation** (optional): "For this project, Option A is recommended because…" or "Either is fine; Option B matches existing usage in `lib/forms`."

### Example

**Context**: Adding client-side form validation for the annotation editor.

| Option | Pros | Cons |
|--------|------|------|
| **Zod + react-hook-form** | Matches project stack; good TypeScript inference | Slightly more setup |
| **HTML5 + `setCustomValidity`** | No extra deps; simple | Less flexible; weaker typing |
| **Formik + Yup** | Familiar to many | Different from project’s Zod usage; more boilerplate |

**Recommendation**: Use Zod with react-hook-form to stay consistent with existing validation and form patterns in the codebase.

## Quick Reference

- **Do**: Surface 2–4 alternatives, state trade-offs, align with project conventions, recommend when one option is clearly better.
- **Don’t**: Suggest alternatives that contradict project rules, list every possible option, or refactor to an alternative without the user asking.
