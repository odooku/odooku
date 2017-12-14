from setuptools import setup, find_packages

try:
    import pypandoc
    long_description = pypandoc.convert('README.md', 'rst')
except(IOError, ImportError):
    long_description = open('README.md').read()

setup(
    name='odooku',
    version='11.0.2',
    url='https://github.com/odooku/odooku',
    author='Raymond Reggers - Adaptiv Design',
    author_email='raymond@adaptiv.nl',
    description=('Odooku'),
    long_description=long_description,
    license='Apache Software License',
    packages=find_packages(),
    namespace_packages=[
        'odooku_addons',
        'odooku_commands',
        'odooku_patches'
    ],
    include_package_data=True,
    zip_safe=False,
    python_requires='>=3.5',
    install_requires=[
        'boto3>=1.4.0',
        'click==6.6',
        'redis==2.10.5',
        'bpython==0.15.0',
        'gevent==1.2.2',
        'psycogreen==1.0',
        'gevent-websocket==0.10.1'
    ],
    entry_points='''
        [console_scripts]
        odooku=odooku.cli.main:entrypoint
    ''',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Programming Language :: Python :: 3.5',
        'License :: OSI Approved :: Apache Software License',
    ],
)
