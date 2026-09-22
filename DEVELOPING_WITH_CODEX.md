# Developing this website with Codex

This guide is for collaborators who want to update the website without needing
to know much about HTML, Python, or Git. Codex can make the changes and run the
commands; your role is to describe the desired result, review it in a browser,
and approve what gets published.

## First-time setup

If the project is already open in Codex and `git status` works, skip to
[Before you start](#before-you-start).

### 1. Get access

Ask the repository owner to add your GitHub account as a collaborator on
`Gin01234i/juliahung`. Accept the invitation from GitHub before trying to push.

You will need accounts for:

- [GitHub](https://github.com/) to download and publish the website.
- ChatGPT/Codex to work on the local files. Follow the
  [official Codex documentation](https://developers.openai.com/codex/) to
  install Codex and sign in.

You do not need an OpenAI API key for this workflow.

### 2. Install Git

Download Git from [git-scm.com](https://git-scm.com/downloads) and use the
standard installation options. On macOS, entering `git --version` in Terminal
may also offer to install Apple's command-line developer tools, which include
Git.

After installation, open Terminal and check:

```bash
git --version
```

It should print a version number rather than an error.

Set the name and email that will appear on your commits. Use the email attached
to your GitHub account:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

### 3. Install Python 3

Download Python 3 from [python.org](https://www.python.org/downloads/). On
Windows, select **Add Python to PATH** in the installer. Then check:

```bash
python3 --version
```

On Windows, use `py -3 --version` if `python3` is not recognized. The command
should report Python 3. This project uses Python only for its local web server
and site-checking tools; there are no packages to install.

### 4. Set up GitHub authentication

GitHub does not accept your account password from `git push`. The easiest
command-line setup is [GitHub CLI](https://cli.github.com/):

1. Install GitHub CLI for your operating system.
2. Open Terminal and run `gh auth login`.
3. Choose **GitHub.com**, **HTTPS**, and **Login with a web browser**.
4. Run `gh auth setup-git` after login.

Confirm the connection:

```bash
gh auth status
```

Never paste an access token, password, or private key into a Codex prompt or a
file in this repository.

### 5. Download the website

Choose a folder where you keep projects, then clone the repository:

```bash
cd ~/Documents
git clone https://github.com/Gin01234i/juliahung.git
cd juliahung
```

On Windows, you can choose a folder in File Explorer, right-click it, select
**Open in Terminal**, and run the last two commands. If the repository is
private, complete the browser sign-in when prompted.

You only clone once. On later days, open this existing `juliahung` folder and
pull the latest changes instead of cloning another copy.

### 6. Open the repository in Codex

Open Codex, sign in, and choose the local `juliahung` folder as the workspace.
Start a task and ask:

> Check the repository setup. Confirm that Git and Python are available, show
> me the current branch and status, and run the site checks. Do not change any
> files yet.

If those checks pass, setup is complete. Codex may ask permission before using
the network, modifying Git history, or pushing; review the requested action and
approve it only when it matches your task.

## Before you start

You need:

- Codex with this repository open.
- Python 3, which is included with the development setup used for this site.
- Access to the GitHub repository so you can pull and push changes.

Open the `juliahung` repository in Codex. Before starting a change, ask:

> Check whether my local copy is clean and pull the latest version from GitHub.
> Do not discard any uncommitted work.

Codex should report the current branch and warn you if local work could conflict
with the pull. Never ask it to discard changes unless you are certain they are
no longer needed.

## Make a change

Describe the result in everyday language. Include the page, the old content,
and the desired new content when possible. For example:

> On the About page, change the first paragraph to: “…” Keep the existing
> typography and spacing. Show me the files changed and run the site checks.

Other useful requests:

> Add this exhibition to the Exhibitions page using the existing design. Use
> the attached images in the order provided.

> Replace the contact email address everywhere it appears. Preserve the current
> layout and test all affected links.

> Update the home-page featured exhibition, but do not commit yet.

Ask Codex to explain anything you do not understand. It should not require you
to translate your request into code.

## Preview changes locally

A local preview lets you review the website before publishing it. In Codex,
ask:

> Start a local server for this website and tell me which address to open.

The underlying command, run from the repository folder, is:

```bash
python3 -m http.server 8000
```

Open <http://localhost:8000> in a browser. Keep the terminal running while you
review the site. Refresh the browser after each change. To stop the server,
return to its terminal and press `Control-C`.

To reproduce the GitHub Pages review address more closely, serve the directory
that contains the repository:

```bash
cd ..
python3 -m http.server 8000
```

Then open <http://localhost:8000/juliahung/>. This checks that links and images
work when the site is under `/juliahung/`, as they are on GitHub Pages.

The server is only visible on your computer and does not publish anything.

## Check the work

Before committing, ask Codex:

> Review the diff, run all relevant site checks, and summarize anything that
> could affect another page. Do not commit yet.

The main automated checks are:

```bash
python3 tools/check_site.py
python3 tools/relativize.py --check
```

`check_site.py` checks internal links, shared navigation, old Wix references,
and image descriptions. `relativize.py --check` verifies that the same site can
work both at the GitHub Pages `/juliahung/` path and later at `jujuhung.com`.

For the broader URL check, keep the local server running and use:

```bash
python3 tools/check_urls.py
```

Automated checks are helpful, but also inspect the changed pages on both a wide
desktop window and a narrow mobile-sized window.

## Pull, commit, and push

These three Git operations have different purposes:

- **Pull** downloads other people's latest changes from GitHub.
- **Commit** saves a named snapshot in your local repository.
- **Push** uploads local commits to GitHub and starts the Pages deployment.

Use this sequence:

1. Pull before beginning the change.
2. Make and preview the change.
3. Review the diff and run the checks.
4. Commit only the files related to the change.
5. Push the commit to GitHub.

A complete request to Codex can be:

> Pull the latest `main` branch without overwriting local work. Make the change
> we discussed, preview and test it, show me a summary, then commit it with a
> clear message and push it to `origin/main`.

The equivalent commands are:

```bash
git pull --ff-only origin main
git status
git diff
python3 tools/check_site.py
python3 tools/relativize.py --check
git add <only the files that belong to this change>
git commit -m "Describe the change clearly"
git push origin main
```

Avoid `git add .` unless you have reviewed every changed file. It can include
unrelated work by accident. Do not commit passwords, API keys, private contact
details, or full-resolution source files from `_archive/`.

If Git reports a conflict, authentication error, or rejected push, stop and ask
Codex to explain the exact problem. Do not use `git reset --hard` or force-push
as a quick fix; both can destroy other people's work.

## After pushing

GitHub Pages needs a short time to deploy. Open the repository's **Actions** tab
on GitHub and wait for the Pages workflow to turn green. Then review:

<https://gin01234i.github.io/juliahung/>

Use a private browser window or force-refresh if an old stylesheet or image is
cached. A successful push only proves that deployment ran; check the updated
page itself before considering the change complete.

## A safe everyday prompt

This prompt covers the normal workflow:

> Update [page or content] so that [desired result]. Preserve the existing
> visual style. First pull the latest changes without discarding local work.
> After editing, run the site and relative-path checks and tell me how to preview
> the affected page locally. Show me the diff summary before committing. Once I
> approve it, commit only the relevant files and push to `origin/main`.
