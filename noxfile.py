import nox


@nox.session(python=['3.10'])
def tests(session):
    session.install('.[test,toml]', 'coverage')
    session.run('coverage', 'run', '-m', 'ward', *session.posargs)
    session.run('coverage', 'json')
