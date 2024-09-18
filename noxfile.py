"""Tasks using Python environments."""

from pathlib import Path
from typing import cast

import nox
from nox.sessions import Session

# TODO: if/when Python 3.7 support is dropped, prefer uv to venv backend
nox.options.default_venv_backend = 'venv'
nox.options.reuse_existing_virtualenvs = True
ALL_PYTHONS = next(
    filter(
        lambda line: line.startswith('python '),
        (Path(__file__).parent / '.tool-versions').read_text().splitlines(),
    )
).split()[1:]
DEFAULT_PYTHON = '3.12'


@nox.session(python=ALL_PYTHONS)
def test(session: Session):
    """Run all tests."""
    session.install('-U', 'pip')
    session.install('-U', '.[test,toml]', 'coverage')
    session.run('coverage', 'run', '-p', '-m', 'ward', *session.posargs)


@nox.session(python=ALL_PYTHONS)
def test_without_toml(session: Session):
    """Run tests without optional TOML support installed."""
    session.install('-U', 'pip')
    session.install('-U', '.[test-without-toml]', 'coverage')
    session.run('coverage', 'run', '-p', '-m', 'ward', *session.posargs)


@nox.session(python=[DEFAULT_PYTHON])
def combine_coverage(session: Session):
    """Prepare a combined coverage report for uploading."""
    session.install('-U', 'coverage')
    session.run('coverage', 'combine')
    session.run('coverage', 'json')


@nox.session(python=[DEFAULT_PYTHON])
def fmt(session: Session):
    """Format and lint code and docs."""
    session.install('-r', 'fmt-requirements.txt')
    session.run('darglint', 'nt2', 'test')
    for tool in (('ssort',), ('ruff', 'format'), ('ruff', 'check', '--fix'), ('ruff', 'check')):
        session.run(*tool, 'noxfile.py', 'nt2', 'test')


@nox.session(python=[DEFAULT_PYTHON])
def publish(session: Session):
    """Package and upload to PyPI."""
    session.install('-U', '.[dev]')
    session.run('flit', 'publish')


@nox.session(python=[DEFAULT_PYTHON])
def typecheck(session: Session):
    """Check types."""
    session.install('-U', '.[dev]')
    session.run('sh', '-c', 'pyright --outputjson 2>/dev/null | json2nt', external=True)
    session.run('pyright', '--warnings')


@nox.session(python=[DEFAULT_PYTHON])
def render_readme(session: Session):
    """Generate README.md from templates/README.md.wz."""
    session.install('-Ue', '.[doc]')
    content = session.run('wheezy.template', 'templates/README.md.wz', silent=True)
    Path('README.md').write_text(cast(str, content))
    session.run(
        'md_toc', '--in-place', '--skip-lines', '2', 'github', '--header-levels', '4', 'README.md'
    )


@nox.session(python=[DEFAULT_PYTHON])
def render_api_docs(session: Session):
    """Generate doc/api HTML documentation from docstrings."""
    session.install('-r', 'doc/doc-requirements.txt')
    session.run('pydoctor', 'nt2')


@nox.session(python=[DEFAULT_PYTHON])
def lock(session: Session):
    """Generate updated requirements.txt lock files and pyproject.toml."""
    session.install('-U', 'uv')
    for reqsfile in (
        'nt2/requirements.in',
        'nt2/toml-requirements.in',
        'test/test-requirements.in',
        'test/test-without-toml-requirements.in',
        'fmt-requirements.in',
        'dev-requirements.in',
        'doc/doc-requirements.in',
    ):
        rf = Path.cwd() / reqsfile
        with session.chdir(rf.parent):
            session.run(
                'uv',
                'pip',
                'compile',
                '--upgrade',
                '--no-header',
                '--annotation-style=line',
                rf.name,
                '--output-file',
                rf.with_suffix('.txt').name,
            )
    session.run('zsh', '-c', '. ./.zpy/zpy.plugin.zsh; pypc -y', external=True)
