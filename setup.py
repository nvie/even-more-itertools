"""
even-more-itertools: because more-itertools just doesn't cut it.
"""
from setuptools import find_packages, setup

dependencies = ['more_itertools']

setup(
    name='even-more-itertools',
    version='0.0.1',
    url='https://github.com/nvie/even-more-itertools',
    author='Vincent Driessen',
    author_email='me@nvie.com',
    description='Collection of even more itertools.',
    long_description=__doc__,
    packages=find_packages(exclude=['tests']),
    include_package_data=True,
    zip_safe=False,
    platforms='any',
    install_requires=dependencies,
)
