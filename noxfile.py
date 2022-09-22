import nox


@nox.session(python=['3.10'])
def tests(session):
    session.install('.[test,toml]')
    session.run('ward', *session.posargs)
