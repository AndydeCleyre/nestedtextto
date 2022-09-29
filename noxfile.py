import nox


@nox.session(python=['3.10'])
def test(session):
    session.install('.[test,toml]', 'coverage')
    session.run('coverage', 'run', '-m', 'ward', *session.posargs)
    session.run('coverage', 'json')


@nox.session(python=['3.10'])
def fmt(session):
    session.install('-r', 'fmt-requirements.txt')
    session.run('ssort', '.')
    session.run('black', '.')
    session.run('isort', '.')
    session.run('ruff', '.')


@nox.session(python=['3.10'])
def lock(session):
    session.install('pip-tools')
    for reqsfile in (
        'nt2/requirements.in',
        'nt2/toml-requirements.in',
        'test/test-requirements.in',
        'fmt-requirements.in',
        'dev-requirements.in',
    ):
        session.run(
            'pip-compile',
            '--upgrade',
            '--no-header',
            '--annotation-style=line',
            '--strip-extras',
            '--allow-unsafe',
            '--resolver=backtracking',
            reqsfile,
        )
    session.run('zsh', '-c', '. ./.zpy/zpy.plugin.zsh; pypc -y', external=True)
