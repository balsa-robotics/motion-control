add_executable(smoke_test
  smoke_test.cpp
)

target_link_libraries(smoke_test
  PRIVATE
    motion_control::core
    motion_control::warnings
    GTest::gtest_main
)

gtest_discover_tests(smoke_test)
