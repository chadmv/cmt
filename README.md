[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# cmt
cmt is a collection of various Maya tools I have written for my personal projects.  Feel free to use
the tools in your own projects or just browse the code for inspiration or to silently judge me.

Full documentation can be found here: https://chadmv.github.io/cmt

# Plug-in Dependencies
* [Eigen](http://eigen.tuxfamily.org/index.php?title=Main_Page)

# Plug-in Compilation Instructions
Download [Eigen](http://eigen.tuxfamily.org/index.php?title=Main_Page) and extract into `third-party/Eigen`.

The project is setup to use CMake to generate build files.

### Windows
```
mkdir build.2020
cd build.2020
cmake -G "Visual Studio 15 2017 Win64" -DMAYA_VERSION=2020
cmake --build . --target install --config Release
```

# Installation Instructions
cmt is Maya module that can be installed like all other Maya modules.  You can do one of the following:

* Add the cmt root directory to the MAYA_MODULE_PATH environment variable.
* Add the cmt root directory to the MAYA_MODULE_PATH in your Maya.env.  e.g.  MAYA_MODULE_PATH += /path/to/cmt
* Edit the cmt.mod file, and replace the ./ with the full path to the cmt root directory, then copy the cmt.mod file to where your modules are loaded from.
