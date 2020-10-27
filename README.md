[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/ambv/black)

# cmt
cmt is a collection of various Maya tools I have written for my personal projects.  Feel free to use
the tools in your own projects, browse the code for inspiration, or silently judge me. These tools
were never meant to be a professional product. Many areas are undocumented, I'm always experimenting but
feel free to take and use any of the code in this project.

Full documentation can be found here: https://chadmv.github.io/cmt

# Installing the Maya Module

## Download Pre-built Release
Built plug-ins are provided via my [Releases](https://github.com/chadmv/cmt/releases)

## Compile Your Own

### Plug-in Compilation Dependencies
* [Eigen](http://eigen.tuxfamily.org/index.php?title=Main_Page)

### Plug-in Compilation Instructions
Download [Eigen](http://eigen.tuxfamily.org/index.php?title=Main_Page) and extract into `third-party/Eigen`.

The project is setup to use CMake to generate build files.

#### Windows
The build.bat included will build for 2018, 2019 and 2020. Or:

```
mkdir build.2020
cd build.2020
cmake -A x64 -T v141 -DMAYA_VERSION=2020 ../
cmake --build . --target install --config Release
```

# Installation Instructions
cmt is a Maya module that can be installed like all other [Maya modules](http://help.autodesk.com/view/MAYAUL/2020/ENU//?guid=Maya_SDK_MERGED_Distributing_Maya_Plug_ins_Distributing_Multi_File_Modules_html).  You can do one of the following:

* Add the cmt root directory to the MAYA_MODULE_PATH environment variable.
* Add the cmt root directory to the MAYA_MODULE_PATH in your Maya.env.  e.g.  MAYA_MODULE_PATH=/path/to/cmt
* Edit the cmt.mod file, and replace the ./ with the full path to the cmt root directory, then copy the cmt.mod file to where your modules are loaded from.
