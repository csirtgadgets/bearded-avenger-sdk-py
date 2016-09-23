import os
from setuptools import setup, find_packages
import versioneer

# vagrant doesn't appreciate hard-linking
if os.environ.get('USER') == 'vagrant' or os.path.isdir('/vagrant'):
    del os.link

setup(
    name="cifsdk",
    version=versioneer.get_version(),
    cmdclass=versioneer.get_cmdclass(),
    description="CIFv3 SDK",
    long_description="Software Development Kit for CIFv3",
    url="https://github.com/csirtgadgets/bearded-avenger-sdk",
    license='LGPL3',
    classifiers=[
               "Topic :: System :: Networking",
               "Environment :: Other Environment",
               "Intended Audience :: Developers",
               "License :: OSI Approved :: GNU Lesser General Public License v3 (LGPLv3)",
               "Programming Language :: Python",
               ],
    keywords=['security'],
    author="Wes Young",
    author_email="wes@csirtgadgets.org",
    packages=find_packages(),
    install_requires=[
        'PyYAML>=3.11',
        'prettytable>=0.7.2',
        'pyaml>=15.03.1',
        'pyzmq==15.4.0',
        'requests>=2.6.0',
        'urllib3>=1.10.2',
        'csirtg_indicator',
    ],
    scripts=[],
    entry_points={
        'console_scripts': [
            'cif=cifsdk.client:main',
            'cif-tokens=cifsdk.client.tokens:main',
        ]
    },
)
