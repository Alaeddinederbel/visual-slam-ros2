# Your setup.py should include this entry_points section:

from setuptools import setup

package_name = 'my_robot_detection'

setup(
    name=package_name,
    version='0.0.0',
    packages=[package_name],
    data_files=[
        ('share/ament_index/resource_index/packages',
            ['resource/' + package_name]),
        ('share/' + package_name, ['package.xml']),
    ],
    install_requires=['setuptools'],
    zip_safe=True,
    maintainer='your_name',
    maintainer_email='your_email@example.com',
    description='YOLO detection package',
    license='Apache License 2.0',
    tests_require=['pytest'],
    entry_points={
        'console_scripts': [
            'yolov8_detector = my_robot_detection.yoloV8:main',
            # Alternative entries if needed:
            'yoloV8 = my_robot_detection.yoloV8:main',
            'yoloV8.py = my_robot_detection.yoloV8:main',
        ],
    },
)