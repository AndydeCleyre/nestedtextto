from pathlib import Path

import nox


@nox.session(python=['3.7', '3.8', '3.9', '3.10'])
def test(session):
    session.install('.[test,toml]', 'coverage')
    session.run('coverage', 'run', '-p', '-m', 'ward', *session.posargs)


@nox.session(python=['3.7', '3.8', '3.9', '3.10'])
def test_without_toml(session):
    session.install('.[test-without-toml]', 'coverage')
    session.run('coverage', 'run', '-p', '-m', 'ward', *session.posargs)


@nox.session(python=['3.10'])
def combine_coverage(session):
    session.install('coverage')
    session.run('coverage', 'combine')
    session.run('coverage', 'json')


@nox.session(python=['3.10'])
def fmt(session):
    session.install('-r', 'fmt-requirements.txt')
    for tool in ('ssort', 'black', 'isort', 'ruff'):
        session.run(tool, '.')


@nox.session(python=['3.10'])
def render_readme(session):
    with session.chdir('doc'):
        session.install('-r', 'doc-requirements.txt')
    content = session.run('wheezy.template', 'templates/README.md.wz', silent=True)
    Path('README.md').write_text(content)


@nox.session(python=['3.10'])
def lock(session):
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
