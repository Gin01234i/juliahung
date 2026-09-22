# Developing this website with Codex (macOS)

This guide is for collaborators on a Mac who want to update the website without
knowing HTML, Python, or Git. Codex makes the changes and runs the commands;
your job is to describe the result you want, look at it in a browser, and
approve what gets published.

The day-to-day work happens in the **Codex desktop app**. You describe the
change in plain English, Codex does it and shows you what it did, and you
approve it.

Terminal — the black-and-white app where you type commands — appears once,
during first-time setup, to install the tools Codex needs. After that you can
leave it closed. Where this guide does show a command, copy it exactly, press
Return, and read what comes back; you do not need to understand it.

Everything below is written for macOS only.

---

# Part 1 — First-time setup

Do this once, on the Mac you will be working on. Budget about 45 minutes, most
of it waiting for downloads.

Here is what you are setting up and why:

| Piece | What it is for |
| --- | --- |
| A GitHub account | Where the website lives and from where it is published. |
| The Codex app | Where you work: it edits the files and runs the commands. |
| Terminal | Used once, for the installs below. Already on your Mac. |
| Git | Tracks changes to the website files and moves them to and from GitHub. |
| Python 3 | Runs the local preview server and the site-checking scripts. |
| Homebrew | An installer that fetches the tool below. |
| GitHub CLI (`gh`) | Signs your Mac in to GitHub, so Codex can pull and push. |
| A copy of the site | A folder named `juliahung` in your Documents folder. |

## 1. Get a GitHub account and access to the repository

Do this first: the invitation has to come from another person, and you cannot
download the website until you have accepted it.

1. If you do not have an account, sign up at
   [github.com/signup](https://github.com/signup) and verify your email.
2. Send your GitHub username to the repository owner and ask to be added as a
   collaborator on `Gin01234i/juliahung`.
3. You will get an email invitation. **Accept it** — the invitation also shows
   up at <https://github.com/Gin01234i/juliahung/invitations>.

While you wait for the invitation, carry on with the rest of the setup.

## 2. Install the Codex app

Download the Codex app for macOS from the
[official Codex documentation](https://developers.openai.com/codex/), drag it
into your **Applications** folder, and open it.

Sign in with your ChatGPT account when prompted. You do **not** need an OpenAI
API key for this workflow.

Leave the app open; you will point it at the website folder in step 9.

## 3. Open Terminal (the only part of setup that needs it)

Press **Command-Space**, type `Terminal`, and press **Return**. (It also lives
in **Applications → Utilities → Terminal**.)

A window opens with a line of text ending in `%`. That is the prompt; it is
waiting for you.

Three things worth knowing:

- Type or paste one command, then press **Return** to run it. Paste with
  **Command-V**, as in any other Mac app.
- When a command asks for your Mac login password, **nothing appears as you
  type** — no dots, no stars. That is normal. Type it and press Return.
- To copy a command out of this guide, select it and press **Command-C**. Do
  not include the surrounding text.

Keep this window open through step 8.

## 4. Install Apple's developer tools (this gives you Git and Python 3)

In Terminal, run:

```bash
xcode-select --install
```

A dialog appears asking whether to install the command line developer tools.
Click **Install**, agree to the licence, and wait — it is a large download and
can take ten minutes or more.

If instead you see `command line tools are already installed`, you already have
them. Move on.

When it finishes, check both tools:

```bash
git --version
python3 --version
```

You should see something like `git version 2.39.5` and `Python 3.9.6`. Any
version numbers are fine, as long as Python starts with a `3`. If either
command prints `command not found`, see
[Troubleshooting](#troubleshooting) at the end.

This project needs no Python packages, no Node, and no build tools.

## 5. Tell Git who you are

Every change you save is stamped with a name and an email. Use the email
attached to your GitHub account. Run these two commands, substituting your own
details:

```bash
git config --global user.name "Your Name"
git config --global user.email "you@example.com"
```

Nothing is printed. That is success. To confirm:

```bash
git config --global --list
```

## 6. Install Homebrew

Homebrew installs the sign-in tool in the next step. Paste this single long
command into Terminal and press Return:

```bash
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
```

It explains what it will do and waits; press **Return** to continue. It then
asks for your Mac login password (remember: invisible as you type).

When it finishes, read the last few lines of output. On Apple Silicon Macs
(M1 and later) it asks you to run two more commands. If it does, run these:

```bash
echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zprofile
eval "$(/opt/homebrew/bin/brew shellenv)"
```

Check it worked:

```bash
brew --version
```

It should print a version number.

## 7. Sign your Mac in to GitHub

GitHub will not accept your account password from the command line, so this
step sets up proper authentication once. It is what later lets Codex pull and
push on your behalf.

Install GitHub CLI:

```bash
brew install gh
```

Then start the sign-in:

```bash
gh auth login
```

It asks a short series of questions. Use the arrow keys and Return to answer:

1. **What account do you want to log into?** → `GitHub.com`
2. **What is your preferred protocol for Git operations?** → `HTTPS`
3. **Authenticate Git with your GitHub credentials?** → `Yes`
4. **How would you like to authenticate?** → `Login with a web browser`

It then shows a one-time code such as `ABCD-1234`. Copy it, press Return, and
your browser opens GitHub. Paste the code, sign in if asked, and click
**Authorize**. Return to Terminal, which should report a green checkmark and
your username.

Then make sure Git itself uses that sign-in:

```bash
gh auth setup-git
gh auth status
```

`gh auth status` should say you are logged in to github.com as your username.

> **Never** paste an access token, password, recovery code, or private key into
> a Codex prompt or into a file in this repository. The sign-in above is the
> only credential setup you need.

## 8. Download the website

This is the point where the invitation from step 1 has to be accepted. If it
has not arrived yet, chase it before going further.

Pick a folder to keep the site in — Documents is a fine choice — and copy it
down from GitHub:

```bash
cd ~/Documents
git clone https://github.com/Gin01234i/juliahung.git
```

That creates `~/Documents/juliahung`, holding the whole website. To see it in
Finder:

```bash
open ~/Documents/juliahung
```

**You only clone once.** From now on you open that same folder in the Codex app
and pull the latest changes; do not clone a second copy.

You are done with Terminal. You can close that window.

## 9. Open the folder in the Codex app

Switch to the Codex app and open `~/Documents/juliahung` as the folder — the
app's own **Open Folder** control, or dragging the folder from Finder onto the
app, both work. Everything Codex does from now on happens inside that folder.

Then type your first request:

> Check the repository setup. Confirm that Git and Python are available, show
> me the current branch and status, and run the site checks. Do not change any
> files yet.

Codex asks permission before it runs a command, reaches the network, or changes
a file. Read what it is asking for and approve it only when it matches what you
asked for.

If those checks pass, setup is complete.

---

# Part 2 — Everyday use

Everything in this part happens in the Codex app.

## Starting a session

1. Open the Codex app.
2. Make sure the folder it is working in is `~/Documents/juliahung` — the app
   remembers recent folders, so this is usually one click.
3. Before changing anything, ask:

> Check whether my local copy is clean and pull the latest version from GitHub.
> Do not discard any uncommitted work.

Codex should report the current branch and warn you if local work could
conflict with the pull. Never ask it to discard changes unless you are certain
they are no longer needed.

## How Codex asks permission

Codex works on the files in that folder and asks before doing anything beyond
that — running a command, using the network, pushing to GitHub. Each request
tells you what it wants to do.

- If it matches what you asked for, approve it.
- If it does not, decline and ask Codex to explain why it wanted to.

Do not switch the app into a mode that stops asking. The approval step is your
chance to catch a misunderstanding before it reaches the website.

## Make a change

Describe the result in everyday language. Name the page, the old content, and
the new content where you can:

> On the About page, change the first paragraph to: “…” Keep the existing
> typography and spacing. Show me the files changed and run the site checks.

Other useful requests:

> Add this exhibition to the Exhibitions page using the existing design. Use
> the images I put in the folder, in the order I list them.

> Replace the contact email address everywhere it appears. Preserve the current
> layout and test all affected links.

> Update the home-page featured exhibition, but do not commit yet.

Ask Codex to explain anything you do not understand. It should not require you
to translate your request into code.

### Working with images

Codex can only use files it can see. Copy the image files into the `juliahung`
folder in Finder first — a new folder inside it is fine — then tell Codex their
names and what each one is. For example:

> I have put three photographs in `incoming/` named `hall-01.jpg`,
> `hall-02.jpg` and `hall-03.jpg`. Add them to the new exhibition page in that
> order, make the web-sized versions the way the other pages do it, and write
> image descriptions for each.

You can also drag a screenshot into the chat to show Codex what you mean, but a
picture pasted into the chat is a reference, not a file the website can use.

## Preview it on your own Mac

A local preview lets you see the website before anyone else does. Ask:

> Start a local preview server for this website and tell me which address to
> open.

Codex starts the server and gives you an address, normally
<http://localhost:8000>. Open it in your browser, and refresh the page after
each change.

To check the site the way GitHub will serve it, under a `/juliahung/` path, ask:

> Serve the folder above the repository instead, so I can check the site at
> /juliahung/.

Then open <http://localhost:8000/juliahung/>.

When you are finished reviewing, ask Codex to stop the preview server. The
server is visible only on your Mac; previewing publishes nothing.

## Check the work

Before committing, ask Codex:

> Review the diff, run all relevant site checks, and summarize anything that
> could affect another page. Do not commit yet.

The two checks that matter are `check_site.py` — internal links, shared
navigation, old Wix references, image descriptions — and `relativize.py
--check`, which verifies that the same site works both at the GitHub Pages
`/juliahung/` path and at `jujuhung.com`. There is a third, `check_urls.py`,
which needs the preview server running; ask for it when links or page addresses
were part of the change.

Automated checks help, but also look at the changed pages yourself — once in a
wide desktop window, once in a narrow phone-sized one.

## Pull, commit, and push

Three Git operations, with three different jobs:

- **Pull** downloads other people's latest changes from GitHub.
- **Commit** saves a named snapshot on your Mac.
- **Push** uploads your commits to GitHub and starts publishing.

The order:

1. Pull before beginning the change.
2. Make and preview the change.
3. Review the diff and run the checks.
4. Commit only the files related to the change.
5. Push the commit to GitHub.

A complete request to Codex can be:

> Pull the latest `main` branch without overwriting local work. Make the change
> we discussed, preview and test it, show me a summary, then commit it with a
> clear message and push it to `origin/main`.

Two things to insist on when you approve the commit: that it includes **only**
the files belonging to this change, and that it includes no passwords, API
keys, private contact details, or full-resolution originals from `_archive/`.

If Codex reports a conflict, an authentication error, or a rejected push, stop
and ask it to explain the exact problem. Do not approve `git reset --hard` or a
force-push as a quick fix; both can destroy other people's work.

## After pushing

GitHub Pages takes a short while to deploy. Open the repository's **Actions**
tab on GitHub and wait for the Pages workflow to turn green. Then review:

<https://gin01234i.github.io/juliahung/>

Use a private browser window, or force-refresh with **Command-Shift-R**, if an
old stylesheet or image is cached. A successful push only proves that the
deployment ran — check the updated page itself before calling it done.

## A safe everyday prompt

This one prompt covers the normal workflow:

> Update [page or content] so that [desired result]. Preserve the existing
> visual style. First pull the latest changes without discarding local work.
> After editing, run the site and relative-path checks and tell me how to
> preview the affected page locally. Show me the diff summary before
> committing. Once I approve it, commit only the relevant files and push to
> `origin/main`.

---

# Troubleshooting

| What you see | What to do |
| --- | --- |
| Codex says `command not found: git` or `python3` | Step 4 did not complete. Open Terminal, run `xcode-select --install`, and let it finish. |
| `command not found: brew` in Terminal | Run the two `echo`/`eval` commands at the end of step 6, then close and reopen Terminal. |
| `Repository not found` when cloning | You have not accepted the collaborator invitation (step 1), or you are signed in to GitHub as a different account. |
| `Authentication failed`, or Codex is asked for a GitHub password | The sign-in from step 7 is missing or expired. Open Terminal and run `gh auth login`, then `gh auth setup-git`. |
| `! [rejected]` on push | Someone else pushed first. Ask Codex to pull the latest `main` and reconcile — never force-push. |
| `Address already in use` when starting the preview | A preview server is already running. Use the address you already have, or ask Codex to stop the old server first. |
| The preview address shows nothing | The server was stopped, or Codex is serving a different folder. Ask it which folder it is serving and on which port. |
| The browser shows an old version of the page | Force-refresh with Command-Shift-R, or open a private window. |

When in doubt, copy the exact error text into the Codex chat and ask what it
means before doing anything else.

# What Codex is running for you

You never need to type these, but they are what Codex does on your behalf, and
knowing them makes its summaries easier to read.

```bash
python3 -m http.server 8000        # the local preview at localhost:8000
python3 tools/check_site.py        # links, header drift, Wix refs, alt text
python3 tools/relativize.py --check  # paths work at /juliahung/ and at the domain
python3 tools/check_urls.py        # every kept URL resolves (needs the server)

git pull --ff-only origin main     # bring down other people's changes
git status                         # what has changed locally
git diff                           # the changes themselves, line by line
git add <files>                    # stage only this change's files
git commit -m "Describe the change clearly"
git push origin main               # publish
```

# Glossary

- **Terminal** — the Mac app where you type commands; used once, during setup.
- **Repository (repo)** — the folder holding the website and its full history.
- **Clone** — download a copy of the repository for the first time.
- **Pull** — fetch other people's latest changes into your copy.
- **Commit** — save a named snapshot of your changes locally.
- **Push** — upload your commits to GitHub, which publishes the site.
- **Diff** — the list of exactly what changed, line by line.
- **Branch** — a line of work. This project uses one, called `main`.
- **GitHub Pages** — the GitHub service that serves these files as a website.
