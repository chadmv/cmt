configure_file(cmtConfig.h.in cmtConfig.h)

set(SOURCE_FILES
    "pluginMain.cpp"
    "cmtConfig.h.in"
	"common.h"
    "common.cpp"
    "swingTwistNode.h"
    "swingTwistNode.cpp"
    "swingTwistCmd.h"
    "swingTwistCmd.cpp"
    "rbfNode.h"
    "rbfNode.cpp"
)

find_package(Maya REQUIRED)
find_package(Eigen3 REQUIRED)

add_library(${PROJECT_NAME} SHARED ${SOURCE_FILES})

target_link_libraries(${PROJECT_NAME} PRIVATE Maya::Maya Eigen3::Eigen)
target_include_directories(${PROJECT_NAME} 
    PRIVATE Maya::Maya Eigen3::Eigen
    PUBLIC "${CMAKE_CURRENT_BINARY_DIR}" "${CMAKE_CURRENT_SOURCE_DIR}"
)
MAYA_PLUGIN(${PROJECT_NAME})

install(TARGETS ${PROJECT_NAME} ${MAYA_TARGET_TYPE} DESTINATION plug-ins/${MAYA_VERSION})

