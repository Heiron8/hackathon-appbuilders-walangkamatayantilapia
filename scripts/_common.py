from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import json, subprocess, shutil, datetime

ROOT = Path(__file__).resolve().parents[1]
LOCAL = ROOT / '.workspace-local'
ORCH = ROOT / '.orchestrator'

PROFESSIONAL_MODE = 'professional'
HACKATHON_MODE = 'hackathon-24h'
SUPPORTED_OPERATING_MODES = {PROFESSIONAL_MODE, HACKATHON_MODE}
PROFESSIONAL_ARCHITECTURE_SECTIONS = (
    'problem',
    'users',
    'system-boundary',
    'mvp-scope',
    'user-journeys',
    'functional-requirements',
    'non-functional-requirements',
    'modules',
    'data-model',
    'contracts',
    'security',
    'deployment',
    'observability',
    'qa-strategy',
    'ux-wireframes',
    'review',
)
HACKATHON_ARCHITECTURE_SECTIONS = (
    'product-boundary',
    'primary-user-journey',
    'architecture-style',
    'modules-responsibilities',
    'interfaces-contracts',
    'data-flow',
    'persistence-strategy',
    'external-integrations',
    'failure-fallback',
    'security-boundaries',
    'deployment-route',
    'constraint-tradeoffs',
)
ARCHITECTURE_STATUSES = {
    'not_started', 'in_progress', 'review_pending', 'changes_requested', 'approved'
}

@dataclass(frozen=True)
class ArchitectureRelease:
    outcome: str
    message: str

    @property
    def released(self):
        return self.outcome == 'released'

def read_json(path: Path, default=None):
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding='utf-8'))

def require_object(data, label='JSON data'):
    if not isinstance(data, dict):
        raise ValueError(f'{label} must contain a JSON object at its root.')
    return data

def read_json_object(path: Path, default=None, label=None):
    data = read_json(path, default)
    return require_object(data, label or path.name)

def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')

def now_iso():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()

def require_nonempty_string(value, label):
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f'{label} must be a non-empty string.')
    return value.strip()

def require_timestamp(value, label):
    timestamp = require_nonempty_string(value, label)
    candidate = timestamp[:-1] + '+00:00' if timestamp.endswith('Z') else timestamp
    try:
        parsed = datetime.datetime.fromisoformat(candidate)
    except ValueError as exc:
        raise ValueError(f'{label} must be a valid timezone-aware ISO 8601 timestamp.') from exc
    if parsed.tzinfo is None or parsed.utcoffset() is None:
        raise ValueError(f'{label} must be a valid timezone-aware ISO 8601 timestamp.')
    return timestamp

def cmd_exists(name: str) -> bool:
    return shutil.which(name) is not None

def run(cmd, check=False):
    return subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, check=check)

def operating_mode(config=None):
    config = config if config is not None else read_json_object(
        ROOT / 'workspace.config.json', {}, 'workspace.config.json'
    )
    require_object(config, 'workspace.config.json')
    mode = config.get('operating_mode', PROFESSIONAL_MODE)
    if mode not in SUPPORTED_OPERATING_MODES:
        raise ValueError(f'Unsupported operating mode: {mode}')
    return mode

def required_architecture_sections(config=None):
    return (
        HACKATHON_ARCHITECTURE_SECTIONS
        if operating_mode(config) == HACKATHON_MODE
        else PROFESSIONAL_ARCHITECTURE_SECTIONS
    )

def architecture_release(architecture, config):
    try:
        require_object(architecture, 'architecture-state.json')
        mode = operating_mode(config)
    except ValueError as exc:
        return ArchitectureRelease('invalid', str(exc))

    status = architecture.get('status')
    if status not in ARCHITECTURE_STATUSES:
        return ArchitectureRelease('invalid', f'Invalid architecture status: {status!r}.')
    completed = architecture.get('completed_sections', [])
    if not isinstance(completed, list) or any(not isinstance(section, str) or not section for section in completed):
        return ArchitectureRelease('invalid', 'Architecture completed_sections must be a list of names.')
    if len(completed) != len(set(completed)):
        return ArchitectureRelease('invalid', 'Architecture completed_sections contains duplicates.')

    missing = [section for section in required_architecture_sections(config) if section not in completed]
    if missing:
        return ArchitectureRelease(
            'incomplete',
            f'{mode} architecture is incomplete: ' + ', '.join(missing),
        )
    if status != 'approved':
        return ArchitectureRelease('incomplete', 'Architecture requires explicit approval before task release.')

    approval = architecture.get('approval')
    if approval is not None and not isinstance(approval, dict):
        return ArchitectureRelease('invalid', 'Architecture approval must be an object or null.')
    if isinstance(approval, dict):
        try:
            require_nonempty_string(approval.get('approved_by'), 'Architecture approved_by')
            require_timestamp(approval.get('approved_at'), 'Architecture approved_at')
        except ValueError as exc:
            return ArchitectureRelease('invalid', str(exc))
    if mode == HACKATHON_MODE:
        if not isinstance(approval, dict):
            return ArchitectureRelease('invalid', 'Hackathon architecture requires explicit human approval evidence.')
        if approval.get('mode') != mode:
            return ArchitectureRelease('incomplete', 'Hackathon architecture requires approval for the active mode.')
    elif isinstance(approval, dict) and approval.get('mode') not in (None, mode):
        return ArchitectureRelease('incomplete', 'Professional architecture requires approval for the active mode.')

    return ArchitectureRelease('released', 'Architecture is approved for implementation task release.')
