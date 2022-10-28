"""Tasks using Python environments."""

from pathlib import Path

import nox

nox.options.default_venv_backend = 'venv'
nox.options.reuse_existing_virtualenvs = True
ALL_PYTHONS = ['3.7', '3.8', '3.9', '3.10']
DEFAULT_PYTHON = '3.10'


@nox.session(python=ALL_PYTHONS)
def test(session):
    """Run all tests."""
    session.install('.[test,toml]', 'coverage')
    session.run('coverage', 'run', '-p', '-m', 'ward', *session.posargs)


@nox.session(python=ALL_PYTHONS)
def test_without_toml(session):
    """Run tests without optional TOML support installed."""
    session.install('.[test-without-toml]', 'coverage')
    session.run('coverage', 'run', '-p', '-m', 'ward', *session.posargs)


@nox.session(python=[DEFAULT_PYTHON])
def combine_coverage(session):
    """Prepare a combined coverage report for uploading."""
    session.install('coverage')
    session.run('coverage', 'combine')
    session.run('coverage', 'json')


@nox.session(python=[DEFAULT_PYTHON])
def fmt(session):
    """Format and lint code and docs."""
    session.install('-r', 'fmt-requirements.txt')
    for tool in ('ssort', 'black', 'isort', 'ruff'):
        session.run(tool, '.')
    for tool in ('darglint', 'pydocstyle'):
        session.run(tool, 'nt2', 'test')
    session.run('pydocstyle', 'noxfile.py')


@nox.session(python=[DEFAULT_PYTHON])
def publish(session):
    """Package and upload to PyPI."""
    session.install('.[dev]')
    session.run('flit', 'publish')


@nox.session(python=[DEFAULT_PYTHON])
def render_readme(session):
    """Generate README.md from templates/README.md.wz."""
    session.install('-e', '.[doc]')
    content = session.run('wheezy.template', 'templates/README.md.wz', silent=True)
    Path('README.md').write_text(content)


@nox.session(python=[DEFAULT_PYTHON])
def render_api_docs(session):
    """Generate doc/api HTML documentation from docstrings."""
    session.install('-r', 'doc/doc-requirements.txt')
    session.run('pydoctor', 'nt2')


@nox.session(python=[DEFAULT_PYTHON])
def render_license(session):
    """Update year in license."""
    session.install('-r', 'doc/doc-requirements.txt')
    content = session.run('wheezy.template', 'templates/LICENSE.wz', silent=True)
    Path('LICENSE').write_text(content)


@nox.session(python=[DEFAULT_PYTHON])
def lock(session):
    """Generate updated requirements.txt lock files and pyproject.toml."""
    session.install('pip-tools')
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
                'pip-compile',
                '--upgrade',
                '--no-header',
                '--annotation-style=line',
                '--strip-extras',
                '--allow-unsafe',
                '--resolver=backtracking',
                rf.name,
            )
    session.run('zsh', '-c', '. ./.zpy/zpy.plugin.zsh; pypc -y', external=True)
