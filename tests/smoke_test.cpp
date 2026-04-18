#include "motion_control/core.hpp"

#include <gtest/gtest.h>

TEST(smoke, identity_matrix_is_identity) {
  EXPECT_EQ(motion_control::identity_matrix(), Eigen::Matrix3d::Identity());
}
