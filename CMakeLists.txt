cmake_minimum_required(VERSION 3.24)
project(motion_control
  VERSION 0.0.0
  DESCRIPTION "Real-time motion control core for articulated and parallel-linked robots"
  LANGUAGES CXX
)

set(CMAKE_CXX_STANDARD 20)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(CMAKE_CXX_EXTENSIONS OFF)

set(CMAKE_EXPORT_COMPILE_COMMANDS ON)

list(APPEND CMAKE_MODULE_PATH "${CMAKE_CURRENT_SOURCE_DIR}/cmake")

include(CTest)
include(Dependencies)

add_subdirectory(src)

if(BUILD_TESTING)
  add_subdirectory(tests)
endif()
