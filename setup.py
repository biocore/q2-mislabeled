from setuptools import setup, find_packages

import versioneer

setup(
    name="q2-mislabeled",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    packages=find_packages(),
    url="",
    license="BSD-3-Clause",
    description="Assess sample mislabelings",
    entry_points={
        "qiime2.plugins":
        ["q2-mislabeled=q2_mislabeled.plugin_setup:plugin"]
    },
    package_data={
        'q2_mislabeled.tests': [],
        'q2_mislabeled': []
    },
    install_requires=['sourcetracker2 @ https://github.com/'
                      'wasade/sourcetracker2/archive/be_sparse.zip'],
    zip_safe=False,
)
