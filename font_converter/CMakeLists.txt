cmake_minimum_required(VERSION 3.16)

project(NanoFontConverter)

set(CMAKE_CXX_STANDARD 17)
set(CMAKE_EXPORT_COMPILE_COMMANDS ON)
set(CMAKE_CXX_STANDARD_REQUIRED ON)

find_package(Freetype REQUIRED)

add_executable(
    nanofont
    main.cpp
)

target_link_libraries(
    nanofont
    PRIVATE
    Freetype::Freetype
)
