---
name: validate-bdrc-etext
description: Validate XML etext files using bdrc-etext-sync, then zip and upload to Google Drive on success. Use when the user provides an IE_ID folder (e.g., IE3KG218) and asks to validate, check, QA, or upload the XML files inside it.
---

# BDRC Etext XML Validation & Upload

Autonomous QA agent that validates XML etext files against BDRC standards, and on success zips the folder and uploads it to Google Drive.

## Workflow

### Step 1: Receive the IE_ID

The user provides an `IE_ID` (e.g., `IE3KG218`). The corresponding folder already exists in the workspace with XML files inside.

### Step 2: Environment Check

**bdrc-etext-sync:** Verify it is available:

```bash
command -v bdrc-etext-sync
```

If missing, install it:

```bash
git clone https://github.com/buda-base/ao_etexts.git /tmp/ao_etexts
cd /tmp/ao_etexts
pip install -e .
```

**rclone:** Verify it is available (needed for Google Drive upload):

```bash
command -v rclone
```

If missing, install it:

```bash
# macOS
brew install rclone

# Linux
curl https://rclone.org/install.sh | sudo bash
```

If rclone has never been configured for Google Drive, see the **First-Time rclone Setup** section below.

### Step 3: Locate the Folder

Resolve the path to the `<IE_ID>` folder, typically at the workspace root:

```
<workspace>/<IE_ID>/
```

Verify the folder exists and contains `.xml` files.

### Step 4: Run Validation

Execute exactly:

```bash
bdrc-etext-sync validate --id <IE_ID> --filesdir <PATH_TO_IE_ID_FOLDER>
```

Capture both stdout and stderr.

### Step 5: Handle Results

#### If validation FAILS (non-zero exit code) — STOP here

Present a failure notice with:
- The exact error output from the tool
- File names, line numbers, and element names flagged
- A concise summary of what needs fixing

**Do not proceed to zip or upload.** The user must fix errors first.

#### If validation PASSES (exit code 0) — continue to Step 6

Tell the user all XML files are correctly formatted. Include the tool's stdout for confirmation. Then proceed.

### Step 6: Zip the Folder

```bash
cd <PARENT_DIR_OF_IE_ID_FOLDER>
zip -r <IE_ID>.zip <IE_ID>/
```

Confirm the zip was created and report its size.

### Step 7: Upload to Google Drive

Upload the zip to the shared BDRC folder:

```bash
rclone copy <IE_ID>.zip gdrive:openclaw_pecha/ --drive-shared-with-me
```

The target Google Drive folder is:
`https://drive.google.com/drive/u/1/folders/1MHA-aAyCNnetYfgx_w7sXwxNGEcjvQmu`

The rclone remote `gdrive` must be pre-configured to point to this folder. See setup below.

After upload completes, confirm success to the user and report the uploaded file name.

## First-Time rclone Setup

This only needs to be done once. Run interactively in a terminal:

```bash
rclone config
```

Follow the prompts:
1. Choose `n` for new remote
2. Name it `gdrive`
3. Select `drive` (Google Drive) as the storage type
4. Leave client_id and client_secret blank (uses rclone defaults)
5. Scope: choose `1` (full access)
6. Leave root_folder_id blank
7. Leave service_account_file blank
8. When asked for auto config, choose `Y` — a browser will open for Google sign-in
9. Choose `n` for shared drive (this is a shared folder, not a shared drive)
10. Confirm with `Y`, then `q` to quit config

After setup, verify access:

```bash
rclone lsd gdrive: --drive-shared-with-me
```

Then configure the target path. The rclone path `gdrive:openclaw_pecha/` should map to the folder at:
`https://drive.google.com/drive/u/1/folders/1MHA-aAyCNnetYfgx_w7sXwxNGEcjvQmu`

Adjust the path in Step 7 if the folder name differs in your Drive.

## Important Notes

- Never modify the XML files during validation — only report findings.
- Always show raw tool output so the user can act on it directly.
- If the tool reports warnings (but exit code 0), still surface them before proceeding.
- If the rclone upload fails (auth error, network issue), show the error and suggest re-running `rclone config`.
