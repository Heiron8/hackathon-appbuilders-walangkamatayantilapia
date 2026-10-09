from __future__ import annotations

import json
import re
import sys

from _common import ORCH, ROOT, architecture_release, cmd_exists, read_json, read_json_object, run, run_network
from onboard_member import IdentityError, resolve_member


MINIMUM_PYTHON = (3, 10)


class BootstrapError(RuntimeError):
    pass


def _command_error(result, fallback: str) -> str:
    return (result.stderr or result.stdout or fallback).strip().splitlines()[-1]


def _github_repo_from_remote(remote: str) -> str | None:
    match = re.search(r"github\.com[/:]([^/]+)/([^/]+?)(?:\.git)?$", remote.strip())
    return f"{match.group(1)}/{match.group(2)}" if match else None


def intended_repository(config: dict) -> str | None:
    github = config.get("github", {})
    owner, repo = github.get("owner"), github.get("repo")
    if bool(owner) != bool(repo):
        raise BootstrapError("GitHub configuration requires both github.owner and github.repo.")
    if owner and repo:
        return f"{owner}/{repo}"
    remote = run(["git", "remote", "get-url", "origin"])
    return _github_repo_from_remote(remote.stdout) if remote.returncode == 0 else None


def check_prerequisites() -> None:
    if not cmd_exists("git"):
        raise BootstrapError("Git is required. Install Git, reopen the terminal, and rerun bootstrap.")
    if sys.version_info < MINIMUM_PYTHON:
        required = ".".join(str(part) for part in MINIMUM_PYTHON)
        raise BootstrapError(f"Python {required} or newer is required.")
    if not cmd_exists("gh"):
        raise BootstrapError("GitHub CLI is required. Install gh, reopen the terminal, and rerun bootstrap.")


def check_project_update_access(github: dict) -> None:
    query = """query($owner:String!, $repo:String!, $number:Int!) {
      repository(owner:$owner, name:$repo) { owner {
        ... on User { projectV2(number:$number) { viewerCanUpdate } }
        ... on Organization { projectV2(number:$number) { viewerCanUpdate } }
      } }
    }"""
    result = run([
        "gh", "api", "graphql",
        "-f", f"owner={github['owner']}",
        "-f", f"repo={github['repo']}",
        "-F", f"number={github['project_number']}",
        "-f", f"query={query}",
    ])
    if result.returncode != 0:
        raise BootstrapError(
            f"GitHub Project access is required: {_command_error(result, 'project access failed')}"
        )
    try:
        data = json.loads(result.stdout)
        can_update = data["data"]["repository"]["owner"]["projectV2"]["viewerCanUpdate"]
    except (json.JSONDecodeError, KeyError, TypeError):
        raise BootstrapError("GitHub Project access response was incomplete.")
    if can_update is not True:
        raise BootstrapError("GitHub Project update permission is required for task claiming.")


def check_github_access(config: dict) -> tuple[str, list[dict] | None]:
    auth = run(["gh", "auth", "status"])
    if auth.returncode != 0:
        raise BootstrapError("GitHub authentication required: run `gh auth login`.")
    user = run(["gh", "api", "user", "--jq", ".login"])
    login = user.stdout.strip()
    if user.returncode != 0 or not login:
        raise BootstrapError("Authenticated GitHub username could not be resolved; rerun `gh auth login`.")

    repository = intended_repository(config)
    if repository:
        access = run(["gh", "repo", "view", repository, "--json", "nameWithOwner"])
        if access.returncode != 0:
            raise BootstrapError(
                f"Authenticated GitHub user {login} cannot read {repository}: "
                f"{_command_error(access, 'repository access failed')}"
            )

    github = config.get("github", {})
    project_number = github.get("project_number")
    if project_number is None:
        return login, ready_issues(config, login)
    if not github.get("owner") or not github.get("repo"):
        raise BootstrapError("GitHub Project configuration requires owner, repo, and project_number.")
    try:
        check_project_update_access(github)
        from github_project import items

        project_items = items()
    except (BootstrapError, SystemExit) as exc:
        print(f"GitHub Project unavailable; using Issues-first workflow: {exc}")
        return login, ready_issues(config, login)
    return login, project_items


def ready_issues(config, login):
    repository = intended_repository(config)
    if not repository:
        return []
    result = run_network(['gh', 'issue', 'list', '--repo', repository, '--state', 'open',
                          '--assignee', login, '--label', 'status:ready', '--limit', '100',
                          '--json', 'url,assignees,labels'])
    if result.returncode != 0:
        print('GitHub Issue readiness unavailable; no Ready claim inferred.')
        return []
    try:
        tasks = json.loads(result.stdout)
        ready = config.get('github', {}).get('status_values', {}).get('ready', 'Ready')
        return [{'status': ready, 'content': {'url': task['url']}} for task in tasks
                if [a['login'].lower() for a in task['assignees']] == [login.lower()]
                and [label['name'] for label in task['labels'] if label['name'].startswith('status:')]
                == ['status:ready']]
    except (ValueError, KeyError, TypeError):
        print('GitHub Issue readiness response invalid; no Ready claim inferred.')
        return []


def run_existing_script(script_name: str, label: str) -> None:
    result = run([sys.executable, "-B", f"scripts/{script_name}"])
    if result.stdout:
        print(result.stdout.rstrip())
    if result.returncode != 0:
        raise BootstrapError(f"{label} failed: {_command_error(result, label + ' failed')}")


def classify_readiness(config: dict, project_items: list[dict] | None) -> tuple[str, str]:
    state = read_json_object(ORCH / "project-state.json", {}, "project-state.json")
    architecture = read_json(ORCH / "architecture-state.json", {})
    phase = state.get("project", {}).get("phase", "new")
    release = architecture_release(architecture, config)
    if release.outcome == "invalid":
        raise BootstrapError(f"Architecture state is invalid: {release.message}")
    ready_name = config.get("github", {}).get("status_values", {}).get("ready", "Ready")
    has_ready_task = any(
        item.get("status") == ready_name and (item.get("content") or {}).get("url")
        for item in (project_items or [])
    )
    if phase == "implementation" and release.released and has_ready_task:
        return "READY TO CLAIM", "A Ready task is available; use the task-claim workflow."
    if not release.released:
        return "READY FOR ARCHITECTURE", release.message
    if phase != "implementation":
        return "READY FOR ARCHITECTURE", f"Move the approved project into implementation before claiming tasks (current phase: {phase})."
    return "READY FOR ARCHITECTURE", "Publish or move an approved task to Ready before claiming work."


def main() -> int:
    print("Professional AI Workspace bootstrap")
    print(f"Root: {ROOT}")
    try:
        check_prerequisites()
        run_existing_script("project_sync.py", "Project Sync")
        config = read_json_object(ROOT / "workspace.config.json", {}, "workspace.config.json")
        login, project_items = check_github_access(config)
        member = resolve_member(login)
        print(f"[OK] Identity: {member['name']} ({member['id']}, @{member['github']})")
        run_existing_script("install_hooks.py", "Git hook installation")
        run_existing_script("verify_workspace.py", "Workspace verification")
        state, action = classify_readiness(config, project_items)
    except (BootstrapError, IdentityError, OSError, ValueError) as exc:
        print(f"\nNOT READY\n{exc}")
        return 1

    print(f"\n{state}\n{action}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
