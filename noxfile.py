import nox

@nox.session(python=False)
def tests(session):
    session.env["DJANGO_SETTINGS_MODULE"] = "test_settings"
    session.env["PYTHONPATH"] = "../edx-platform"
    session.run("pytest", "openedx_pok")

@nox.session(python=False)
def coverage(session):
    session.env["DJANGO_SETTINGS_MODULE"] = "test_settings"
    session.env["PYTHONPATH"] = "../edx-platform"
    session.run("pytest", "--cov=openedx_pok", "--cov-report=html")

@nox.session(python=False)
def quality(session):
    session.run("pylint", "openedx_pok", "tests", "manage.py", "setup.py")
    session.run("pycodestyle", "openedx_pok", "tests", "manage.py", "setup.py")
    session.run("pydocstyle", "openedx_pok", "tests", "manage.py", "setup.py")
    session.run(
        "isort", "--check-only", "--diff",
        "openedx_pok", "tests", "manage.py", "setup.py", "openedx_pok/test_settings.py"
    )

@nox.session(python=False)
def pii_check(session):
    session.run(
        "code_annotations", "django_find_annotations",
        "--config_file", ".pii_annotations.yml",
        "--lint", "--report", "--coverage"
    )
