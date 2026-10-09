from __future__ import annotations

from pathlib import Path

from _common import LOCAL, ORCH, cmd_exists, read_json, run, write_json


class IdentityError(ValueError):
    pass


def _normalized(value: str | None) -> str:
    return (value or "").strip().casefold()


def validate_members(members: list[dict]) -> None:
    if not isinstance(members, list):
        raise IdentityError("Shared team members must be a list.")
    for index, member in enumerate(members, 1):
        if not isinstance(member, dict):
            raise IdentityError(f"Shared member {index} must be an object.")
        for field in ("id", "name", "role", "status"):
            if not isinstance(member.get(field), str) or not member[field].strip():
                raise IdentityError(f"Shared member {index} requires a non-empty {field}.")
        github = member.get("github")
        if github is not None and (not isinstance(github, str) or not github.strip()):
            raise IdentityError(f"Shared member {index} GitHub username must be a non-empty string when present.")

    ids = [_normalized(member.get("id")) for member in members]
    duplicate_ids = sorted({member_id for member_id in ids if ids.count(member_id) > 1})
    if duplicate_ids:
        raise IdentityError(f"Duplicate member ID: {duplicate_ids[0]}")

    usernames = [_normalized(member.get("github")) for member in members if member.get("github")]
    duplicate_usernames = sorted({username for username in usernames if usernames.count(username) > 1})
    if duplicate_usernames:
        raise IdentityError(f"Duplicate GitHub username: {duplicate_usernames[0]}")


def validate_team(team) -> None:
    if not isinstance(team, dict):
        raise IdentityError("team.json must contain a JSON object at its root.")
    members = team.get("members", [])
    validate_members(members)
    lead_id = team.get("lead_architect_member_id")
    if lead_id is not None and (
        not isinstance(lead_id, str)
        or _normalized(lead_id) not in {_normalized(member["id"]) for member in members}
    ):
        raise IdentityError("lead_architect_member_id must reference a shared member.")


def stable_member_id(github_username: str) -> str:
    username = _normalized(github_username)
    if not username or any(character not in "abcdefghijklmnopqrstuvwxyz0123456789-" for character in username):
        raise IdentityError("GitHub username must contain only letters, numbers, or hyphens.")
    return f"member-gh-{username}"


def authenticated_github_username() -> str | None:
    if not cmd_exists("gh") or run(["gh", "auth", "status"]).returncode != 0:
        return None
    result = run(["gh", "api", "user", "--jq", ".login"])
    return result.stdout.strip() if result.returncode == 0 and result.stdout.strip() else None


def resolve_member(
    github_username: str | None = None,
    *,
    team_path: Path | None = None,
    local_path: Path | None = None,
    input_fn=None,
    output_fn=print,
) -> dict:
    """Resolve one shared member and set the ignored local identity."""
    team_path = team_path or ORCH / "team.json"
    local_path = local_path or LOCAL / "member.json"
    input_fn = input_fn or input

    team = read_json(team_path, {"lead_architect_member_id": None, "members": []})
    validate_team(team)
    members = team.get("members", [])

    login = _normalized(github_username)
    local = read_json(local_path, {}) or {}
    if not isinstance(local, dict):
        raise IdentityError("Local member identity must contain a JSON object at its root.")
    local_id = _normalized(local.get("member_id"))
    local_member = next((member for member in members if _normalized(member.get("id")) == local_id), None)
    github_member = next((member for member in members if _normalized(member.get("github")) == login), None) if login else None

    if local_id and not local_member:
        raise IdentityError(
            f"Local member ID {local.get('member_id')} is not present in the shared team registry. "
            "Remove or repair .workspace-local/member.json, then rerun bootstrap."
        )
    if local_member and github_member and local_member is not github_member:
        raise IdentityError(
            f"GitHub user {github_username} and local member {local_member.get('id')} map to different shared members."
        )
    if github_member:
        member = github_member
    elif local_member:
        member_login = _normalized(local_member.get("github"))
        if login and member_login != login:
            raise IdentityError(
                f"Local member {local_member.get('id')} belongs to GitHub user "
                f"{local_member.get('github') or '(unconfigured)'}, not {github_username}."
            )
        member = local_member
    else:
        output_fn("Member onboarding (this does NOT grant GitHub repository access).")
        for index, existing in enumerate(members, 1):
            output_fn(
                f"{index}. {existing['name']} ({existing.get('github', 'no-github')}) "
                f"[{existing.get('status', 'active')}]"
            )
        choice = input_fn("Select existing member number, or press Enter to register a new member: ").strip()
        if choice:
            try:
                selected_index = int(choice) - 1
                if selected_index < 0:
                    raise IndexError
                member = members[selected_index]
            except (ValueError, IndexError):
                raise IdentityError("Select a valid existing member number.")
            if login and _normalized(member.get("github")) != login:
                raise IdentityError(
                    f"Selected member {member.get('id')} does not match authenticated GitHub user {github_username}."
                )
        else:
            name = input_fn("Name: ").strip()
            selected_github = github_username or input_fn("GitHub username: ").strip()
            role = input_fn("Role [full-stack]: ").strip() or "full-stack"
            if not name:
                raise IdentityError("Member name is required.")
            if not selected_github:
                raise IdentityError("GitHub username is required.")
            if any(_normalized(existing.get("github")) == _normalized(selected_github) for existing in members):
                raise IdentityError(f"GitHub username {selected_github} already belongs to a shared member.")
            member_id = stable_member_id(selected_github)
            if any(_normalized(existing.get("id")) == _normalized(member_id) for existing in members):
                raise IdentityError(f"Member ID {member_id} already exists.")
            member = {
                "id": member_id,
                "name": name,
                "github": selected_github,
                "role": role,
                "status": "active",
            }
            members.append(member)
            if role == "lead-architect" and not team.get("lead_architect_member_id"):
                team["lead_architect_member_id"] = member["id"]
            write_json(team_path, team)

    local_path.parent.mkdir(parents=True, exist_ok=True)
    write_json(local_path, {"member_id": member["id"]})
    output_fn(f"Local identity set to {member['name']} ({member['id']}).")
    return member


def main() -> int:
    try:
        resolve_member(authenticated_github_username())
    except IdentityError as exc:
        print(f"Identity conflict: {exc}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
