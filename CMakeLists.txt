cmake_minimum_required(VERSION 3.15...3.30)

project(
  ${SKBUILD_PROJECT_NAME}
  LANGUAGES C
  VERSION ${SKBUILD_PROJECT_VERSION})

add_library(crc16_lib SHARED ${CMAKE_CURRENT_SOURCE_DIR}/update_app_unpacker/crc_lib/crc16_lib.c)

install(TARGETS crc16_lib DESTINATION update_app_unpacker/crc_lib/)
