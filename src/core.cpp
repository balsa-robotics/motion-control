#include "motion_control/core.hpp"

namespace motion_control {

Eigen::Matrix3d identity_matrix() {
  return Eigen::Matrix3d::Identity();
}

} // namespace motion_control
