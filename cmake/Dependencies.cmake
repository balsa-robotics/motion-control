find_package(Eigen3 3.4...<6 CONFIG QUIET)
if(NOT Eigen3_FOUND)
  message(FATAL_ERROR
    "Eigen3 (>= 3.4) not found.\n"
    "  Ubuntu: sudo apt install libeigen3-dev\n"
    "  macOS:  brew install eigen\n"
    "See README.md for the full prerequisite list."
  )
endif()

if(BUILD_TESTING)
  find_package(GTest QUIET)
  if(NOT GTest_FOUND)
    message(FATAL_ERROR
      "GoogleTest not found.\n"
      "  Ubuntu: sudo apt install libgtest-dev libgmock-dev\n"
      "  macOS:  brew install googletest\n"
      "See README.md for the full prerequisite list."
    )
  endif()
  include(GoogleTest)
endif()
