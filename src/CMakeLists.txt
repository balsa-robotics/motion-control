add_library(motion_control_warnings INTERFACE)
target_compile_options(motion_control_warnings INTERFACE
  -Wall -Wextra -Wpedantic
  $<$<BOOL:${MOTION_CONTROL_WERROR}>:-Werror>
)
add_library(motion_control::warnings ALIAS motion_control_warnings)

add_library(motion_control_core STATIC
  core.cpp
)
add_library(motion_control::core ALIAS motion_control_core)

target_include_directories(motion_control_core
  PUBLIC
    $<BUILD_INTERFACE:${CMAKE_SOURCE_DIR}/include>
)

target_link_libraries(motion_control_core
  PUBLIC
    Eigen3::Eigen
  PRIVATE
    motion_control::warnings
)
