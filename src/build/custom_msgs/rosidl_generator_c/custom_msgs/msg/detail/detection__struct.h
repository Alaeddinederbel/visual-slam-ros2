// generated from rosidl_generator_c/resource/idl__struct.h.em
// with input from custom_msgs:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef CUSTOM_MSGS__MSG__DETAIL__DETECTION__STRUCT_H_
#define CUSTOM_MSGS__MSG__DETAIL__DETECTION__STRUCT_H_

#ifdef __cplusplus
extern "C"
{
#endif

#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>


// Constants defined in the message

// Include directives for member types
// Member 'header'
#include "std_msgs/msg/detail/header__struct.h"
// Member 'class_name'
#include "rosidl_runtime_c/string.h"
// Member 'bbox'
#include "sensor_msgs/msg/detail/region_of_interest__struct.h"

/// Struct defined in msg/Detection in the package custom_msgs.
typedef struct custom_msgs__msg__Detection
{
  std_msgs__msg__Header header;
  rosidl_runtime_c__String class_name;
  float score;
  /// x_offset, y_offset, width, height
  sensor_msgs__msg__RegionOfInterest bbox;
} custom_msgs__msg__Detection;

// Struct for a sequence of custom_msgs__msg__Detection.
typedef struct custom_msgs__msg__Detection__Sequence
{
  custom_msgs__msg__Detection * data;
  /// The number of valid items in data
  size_t size;
  /// The number of allocated items in data
  size_t capacity;
} custom_msgs__msg__Detection__Sequence;

#ifdef __cplusplus
}
#endif

#endif  // CUSTOM_MSGS__MSG__DETAIL__DETECTION__STRUCT_H_
