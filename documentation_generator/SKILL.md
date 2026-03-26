# Open Claw Skill: OpenPecha README Generator

## Identity
**Name:** openpecha-readme-generator
**Description:** Automatically crawls the OpenPecha GitHub organization to generate standardized README documentation based on TGDP templates and repository analysis.

## Configuration
- **Organization:** `OpenPecha`
- **Template Source:** `https://gitlab.com/tgdp/templates/-/tree/main/readme`
- **Output Filename:** `openclaw_documentation_README.md`
- **Auth:** Requires GitHub PAT with `repo` and `read:org` scopes.

## Execution Logic

### 1. Discovery Phase
- **Target:** `https://github.com/OpenPecha`
- **Action:** Iterate through all repositories within the organization.
- **Criteria:** Process all active repositories; ignore archived ones unless explicitly instructed.

### 2. Analysis Phase
For each repository, the agent must analyze:
- **Project Name & Description:** From GitHub metadata.
- **Tech Stack:** Identify languages and frameworks (e.g., Python, TypeScript, Shell).
- **Installation:** Extract from `requirements.txt`, `setup.py`, `pyproject.toml`, or `package.json`.
- **Project Structure:** Map the top-level directories to understand the codebase layout.
- **Current Docs:** Read existing `README.md` or `/docs` folder to extract high-level context.

### 3. Generation Phase
Generate content mapping the analyzed data to the **TGDP Template Structure**:
- **Title & Badges:** Project name and relevant status badges.
- **Introduction:** A concise summary of what the tool/data does.
- **Installation:** Step-by-step guide based on detected dependency files.
- **Usage:** Basic commands or API examples inferred from the code.
- **Directory Structure:** A tree-view of the repository.
- **Contributing:** Standard link to OpenPecha contribution guidelines.

### 4. Deployment Phase
- **Action:** Create or Update the file.
- **Path:** `{repo_root}/openclaw_documentation_README.md`
- **Commit Message:** `docs: automated readme generation via Open Claw (TGDP Template)`

## Constraints & Safety
- **Non-Destructive:** Do **not** overwrite the original `README.md`.
- **API Respect:** Implement exponential backoff if GitHub API rate limits are hit.
- **No Hallucination:** If the purpose of a repository is unclear from the code, tag the Introduction section with `[Needs Manual Review]`.
