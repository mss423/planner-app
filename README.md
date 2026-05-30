# AI Research Planner

A terminal-based (TUI) research management tool for scientists and academics. Organizes projects, tasks, literature, and meetings in a plain-file backend, with an optional Claude-powered daily scheduling assistant.

## Features

- **Project management** — one directory per project; browse, create, and delete projects from a single screen
- **Task tracking** — per-project tasks with priority, deadline, time estimate, and status (open / in progress / done)
- **Literature tracking** — paper entries with title, authors, year, venue, and read status; open PDFs directly from the TUI
- **Notes** — create and open Markdown/LaTeX notes in your preferred `$EDITOR`
- **Meetings** — one-time and recurring (daily, weekly) meetings; shown alongside tasks in the planning view
- **Weekly calendar** — 7-column week view showing all meetings and task deadlines; step forward/back by week
- **Daily planning** — compose a day's work from open tasks across all projects; navigate between days
- **AI scheduling** — sends your task list and today's meetings to Claude (Sonnet 4.6) and receives a time-blocked schedule with a prioritization rationale

All data is stored as plain YAML and Markdown files — no database, fully portable, git-friendly.

## Requirements

- Python 3.11+
- An [Anthropic API key](https://console.anthropic.com/) (only required for AI scheduling)

## Quick Start

```bash
git clone <repo-url>
cd ai-planner
pip install -e .
planner
```

The first launch opens a setup wizard that asks where to create your research directory (default: `~/Documents/research`). After that, `planner` goes straight to the app.

To enable AI scheduling, set your Anthropic API key before launching:

```bash
export ANTHROPIC_API_KEY=sk-ant-...
planner
```

To reconfigure the research directory at any time:

```bash
planner init                         # interactive prompt
planner init ~/path/to/research      # explicit path
```

## Navigation

Press `?` inside the app for the full keyboard reference. Top-level navigation:

| Key | Screen |
|-----|--------|
| `d` | Dashboard |
| `p` | Projects |
| `n` | Planning |
| `c` | Calendar |
| `m` | Meetings |
| `?` | Help |
| `q` | Quit |

### Dashboard

Home screen. Left panel shows today's meetings and scheduled tasks (with time blocks if AI-scheduled). Right panel shows all deadlines across every project in the next 14 days. Available free time accounts for meeting hours.

### Projects

| Key | Action |
|-----|--------|
| `a` | Create project |
| `Enter` | Open project |
| `D` | Delete project |

### Project Detail

Three tabs — switch with `Tab`.

**Tasks tab**

| Key | Action |
|-----|--------|
| `a` | Add task |
| `e` | Edit selected task |
| `Space` | Toggle done / open |
| `d` | Delete task |
| `f` | Cycle filter (all / open / done) |

**Papers tab**

| Key | Action |
|-----|--------|
| `a` | Add paper |
| `e` | Edit selected paper |
| `o` | Open PDF in system viewer |
| `d` | Delete entry |
| `f` | Cycle filter (all / unread / reading / read) |

**Notes tab**

| Key | Action |
|-----|--------|
| `a` | Create new note (opens in `$EDITOR`) |
| `Enter` | Open selected note in `$EDITOR` |
| `d` | Delete note |

### Planning

| Key | Action |
|-----|--------|
| `Space` | Add / remove task from today's plan |
| `s` | Open AI scheduler |
| `[` / `]` | Go to previous / next day |
| `t` | Jump to today |
| `f` | Cycle project filter |

The left panel lists all open tasks sorted by deadline and priority. Tasks already in the plan are marked with ✓. The right panel shows today's meetings (in blue) and scheduled tasks. The header shows total meeting time and remaining free hours.

### Calendar

Press `c` to open the weekly calendar. Each column represents one day (Mon–Sun) and shows:

- **Blue** — meetings with start time and optional location
- **Colored `▶ DUE:`** — task deadlines, colored by priority
- Today's column is highlighted; past days are dimmed

| Key | Action |
|-----|--------|
| `[` / `]` | Previous / next week |
| `t` | Jump to current week |

### Meetings

| Key | Action |
|-----|--------|
| `a` | Add meeting |
| `e` | Edit selected meeting |
| `d` | Delete meeting |

Recurrence options: **One-time** (specify a date), **Weekly** (check individual days Mon–Sun), **Daily**.

### AI Scheduling

Press `s` on the Planning screen. The modal lets you set:

- **Available hours** — total working hours for the day
- **Preferred start time** — e.g. `09:00`
- **Constraints** — free-text, e.g. `"no deep work before 10am, break at noon"`

Claude receives your tasks (with priorities, deadlines, and estimates), today's fixed meetings (as blocked intervals it must avoid), and your constraints. It returns a time-blocked schedule with a short rationale. Press **Accept** to save it; times will then appear on the Dashboard and Planning view.

## File Structure

```
~/Documents/research/          ← configurable root
  projects/
    <project-name>/
      tasks.yaml               ← task list
      papers.yaml              ← literature entries
      notes/                   ← .md and .tex files
      papers/                  ← PDF files
  planning/
    days/
      YYYY-MM-DD.yaml          ← daily plan + AI schedule
  meetings.yaml                ← all meetings (global)
```

Config is stored at `~/.planner/config.yaml`.

## Data Formats

### tasks.yaml

```yaml
tasks:
  - id: <uuid>
    title: Write intro section
    priority: high          # high | medium | low
    deadline: 2026-06-15
    estimate_hours: 2.0
    status: open            # open | in_progress | done
    created: 2026-05-30
    completed: null
    notes: ""
```

### papers.yaml

```yaml
papers:
  - id: <uuid>
    title: Attention Is All You Need
    authors: Vaswani et al.
    year: 2017
    venue: NeurIPS
    file: papers/attention.pdf   # relative to project dir; null if not downloaded
    status: read                 # unread | reading | read
    added: 2026-05-30
    abstract: ""
    notes: ""
```

### meetings.yaml

```yaml
meetings:
  - id: <uuid>
    title: Group Meeting
    start_time: "14:00"
    end_time: "15:00"
    location: Room 302
    recurrence: weekly           # none | daily | weekly
    days: [0, 2]                 # 0=Mon … 6=Sun (weekly only)
    date: null                   # YYYY-MM-DD (one-time only)
    active: true
    notes: ""
```

### planning/days/YYYY-MM-DD.yaml

```yaml
date: 2026-05-30
available_hours: 6.0
ai_rationale: "Prioritized the NeurIPS deadline..."
schedule:
  - task_id: <uuid>
    project: nlp-research
    start_time: "09:00"
    end_time: "11:00"
    notes: Focus on the related work section first
```
