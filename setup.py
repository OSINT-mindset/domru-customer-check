from setuptools import setup, find_packages

exec(open('domru_customer_check/_version.py').read())

with open('requirements.txt') as rf:
    requires = rf.read().splitlines()

with open('README.md') as fh:
    long_description = fh.read()

setup(
    name="domru_customer_check",
    version=__version__,
    description="A skeleton for OSINT CLI tool",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/soxoj/osint-cli-tool-skeleton",
    author="Soxoj",
    author_email="soxoj@protonmail.com",
    entry_points={'console_scripts': ['domru_customer_check = domru_customer_check.__init__:run']},
    license="MIT",
    packages=find_packages(),
    include_package_data=True,
    install_requires=requires,
)
