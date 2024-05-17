from setuptools import setup, find_packages

setup(
    name='vm',
    version='v1.0.0',
    description='A Project for Version Management',
    author='Kelcin',
    url='https://github.com/Kelcin2/vm',
    packages=find_packages(),
    install_requires=[],
    entry_points={
        'console_scripts': [
            'vm=vm.vm:main',
        ],
    },
    classifiers=[
        'Programming Language :: Python :: 3',
        'License :: OSI Approved :: MIT License',
        'Operating System :: OS Independent',
    ],
    python_requires='>=3.7.4',
)
