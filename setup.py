from setuptools import setup, find_packages

setup(
    name='odooku',
    version='10.0.1',
    url='https://github.com/odooku/odooku',
    author='Raymond Reggers - Adaptiv Design',
    author_email='raymond@adaptiv.nl',
    description=('Odooku'),
    license='Apache Software License',
    packages=find_packages(),
    include_package_data=True,
    zip_safe=False,
    install_requires=[
        'boto3>=1.4.0',
        'click==6.6',
        'redis==2.10.5',
        'bpython==0.15.0',
        'gevent==1.1.2',
        'psycogreen==1.0',
        'gevent-websocket==0.9.5'
    ],
    entry_points='''
        [console_scripts]
        odooku=odooku.cli:entrypoint
    ''',
    classifiers=[
        'Intended Audience :: Developers',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 2',
        'Programming Language :: Python :: 2.7',
        'License :: OSI Approved :: Apache Software License',
    ],
)
