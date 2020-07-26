configure_file(cmtConfig.h.in cmtConfig.h)

set(SOURCE_FILES
    "pluginMain.cpp"
    "cmtConfig.h.in"
	"common.h"
    "common.cpp"
	"linearRegressionSolver.h"
    "linearRegressionSolver.cpp"
    "swingTwistNode.h"
    "swingTwistNode.cpp"
    "swingTwistCmd.h"
    "swingTwistCmd.cpp"
    "demBonesCmd.h"
    "demBonesCmd.cpp"
    "rbfNode.h"
    "rbfNode.cpp"
    "ikRigNode.h"
    "ikRigNode.cpp"
)

SET(DEMBONES_SOURCE
    "DemBones/ConvexLS.h"
    "DemBones/DemBones.h"
    "DemBones/DemBonesExt.h"
    "DemBones/Indexing.h"
    "DemBones/MatBlocks.h"
)
source_group(dembones FILES ${DEMBONES_SOURCE})
find_package(OpenMP)

if (OPENMP_FOUND)
	set (CMAKE_C_FLAGS "${CMAKE_C_FLAGS} ${OpenMP_C_FLAGS}")
	set (CMAKE_CXX_FLAGS "${CMAKE_CXX_FLAGS} ${OpenMP_CXX_FLAGS}")
	set (CMAKE_EXE_LINKER_FLAGS "${CMAKE_EXE_LINKER_FLAGS} ${OpenMP_EXE_LINKER_FLAGS}")
endif()

# Eigen requires /bigobj to compile in DEBUG
add_compile_options("$<$<AND:$<CXX_COMPILER_ID:MSVC>,$<CONFIG:DEBUG>>:/bigobj>")


find_package(Maya REQUIRED)
find_package(Eigen3 REQUIRED)

add_library(${PROJECT_NAME} SHARED ${SOURCE_FILES} ${DEMBONES_SOURCE})

target_link_libraries(${PROJECT_NAME} PRIVATE Maya::Maya Eigen3::Eigen)
target_include_directories(${PROJECT_NAME} 
    PRIVATE Maya::Maya Eigen3::Eigen
    PUBLIC "${CMAKE_CURRENT_BINARY_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}"
)
MAYA_PLUGIN(${PROJECT_NAME})

install(TARGETS ${PROJECT_NAME} ${MAYA_TARGET_TYPE} DESTINATION plug-ins/${MAYA_VERSION})

