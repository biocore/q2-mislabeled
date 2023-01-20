from setuptools import setup, find_packages

import versioneer

long_description = ("q2-mislabeled is a QIIME 2 plugin that facilitates "
                    "detection of mislabeled and contaminated samples. It "
                    "does so by using q2-sample-classifier, and "
                    "SourceTracker2.")


description = ("q2-mislabeled: a QIIME 2 plugin to check sample mislabeling "
               "and contamination")


classes = """
    Development Status :: 4 - Beta
    License :: OSI Approved :: BSD License
    Topic :: Scientific/Engineering :: Bio-Informatics
    Topic :: Software Development :: Libraries :: Application Frameworks
    Topic :: Software Development :: Libraries :: Python Modules
    Programming Language :: Python
    Programming Language :: Python :: 3.8
    Programming Language :: Python :: 3.9
    Programming Language :: Python :: 3.10
    Programming Language :: Python :: Implementation :: CPython
    Operating System :: OS Independent
    Operating System :: POSIX :: Linux
    Operating System :: MacOS :: MacOS X
"""


classifiers = [s.strip() for s in classes.split('\n') if s]
setup(
    name="q2-mislabeled",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    url="",
    license="BSD-3-Clause",
    entry_points={
        "qiime2.plugins":
        ["q2-mislabeled=q2_mislabeled.plugin_setup:plugin"]
    },
    package_data={
        'q2_mislabeled.tests': [],
        'q2_mislabeled': []
    },
    install_requires=['sourcetracker @ https://github.com/'
                      'wasade/sourcetracker2/archive/be_sparse.zip'],
    zip_safe=False,
    long_description=long_description,
    description=description,
    author="Daniel McDonald",
    author_email='d3mcdonald@eng.ucsd.edu',
    maintainer="Daniel McDonald",
    maintainer_email="d3mcdonald@eng.ucsd.edu",
    classifiers=classifiers,
)
