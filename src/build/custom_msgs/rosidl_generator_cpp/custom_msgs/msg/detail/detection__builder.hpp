// generated from rosidl_generator_cpp/resource/idl__builder.hpp.em
// with input from custom_msgs:msg/Detection.idl
// generated code does not contain a copyright notice

#ifndef CUSTOM_MSGS__MSG__DETAIL__DETECTION__BUILDER_HPP_
#define CUSTOM_MSGS__MSG__DETAIL__DETECTION__BUILDER_HPP_

#include <algorithm>
#include <utility>

#include "custom_msgs/msg/detail/detection__struct.hpp"
#include "rosidl_runtime_cpp/message_initialization.hpp"


namespace custom_msgs
{

namespace msg
{

namespace builder
{

class Init_Detection_bbox
{
public:
  explicit Init_Detection_bbox(::custom_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  ::custom_msgs::msg::Detection bbox(::custom_msgs::msg::Detection::_bbox_type arg)
  {
    msg_.bbox = std::move(arg);
    return std::move(msg_);
  }

private:
  ::custom_msgs::msg::Detection msg_;
};

class Init_Detection_score
{
public:
  explicit Init_Detection_score(::custom_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_bbox score(::custom_msgs::msg::Detection::_score_type arg)
  {
    msg_.score = std::move(arg);
    return Init_Detection_bbox(msg_);
  }

private:
  ::custom_msgs::msg::Detection msg_;
};

class Init_Detection_class_name
{
public:
  explicit Init_Detection_class_name(::custom_msgs::msg::Detection & msg)
  : msg_(msg)
  {}
  Init_Detection_score class_name(::custom_msgs::msg::Detection::_class_name_type arg)
  {
    msg_.class_name = std::move(arg);
    return Init_Detection_score(msg_);
  }

private:
  ::custom_msgs::msg::Detection msg_;
};

class Init_Detection_header
{
public:
  Init_Detection_header()
  : msg_(::rosidl_runtime_cpp::MessageInitialization::SKIP)
  {}
  Init_Detection_class_name header(::custom_msgs::msg::Detection::_header_type arg)
  {
    msg_.header = std::move(arg);
    return Init_Detection_class_name(msg_);
  }

private:
  ::custom_msgs::msg::Detection msg_;
};

}  // namespace builder

}  // namespace msg

template<typename MessageType>
auto build();

template<>
inline
auto build<::custom_msgs::msg::Detection>()
{
  return custom_msgs::msg::builder::Init_Detection_header();
}

}  // namespace custom_msgs

#endif  // CUSTOM_MSGS__MSG__DETAIL__DETECTION__BUILDER_HPP_
