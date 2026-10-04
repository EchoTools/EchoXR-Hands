# EchoXR Hands built with CMake: the hand tracking plugin (EchoXRHands.dll), the finger
# bridge (EchoXRHands.exe) and the settings window (EchoXRSettings.exe), into out/ as
# build.bat lays them out. MSVC on Windows, or clang-cl from macOS/Linux:
#
#   cmake -S . -B build -G Ninja -DCMAKE_TOOLCHAIN_FILE=cmake/clang-cl-xwin.cmake
#   cmake --build build
#
# Detours (MIT) is built from its v4.0.1 release, checked by hash, so no detours.lib has
# to be put into third_party/ by hand.

cmake_minimum_required(VERSION 3.20)
# Release unless asked (before project(), which would settle on Debug).
if(NOT DEFINED CMAKE_BUILD_TYPE OR CMAKE_BUILD_TYPE STREQUAL "")
    set(CMAKE_BUILD_TYPE Release CACHE STRING "")
endif()
project(EchoXRHands LANGUAGES C CXX RC)
set(CMAKE_CXX_STANDARD 17)
set(CMAKE_CXX_STANDARD_REQUIRED ON)
set(OUT ${CMAKE_CURRENT_SOURCE_DIR}/out)
file(MAKE_DIRECTORY ${OUT})

# The resource scripts name their files from the repo root with backslashes (build.bat
# runs rc there); llvm-rc off Windows wants forward slashes, so it gets a copy.
function(rc_copy name src)
    file(READ ${CMAKE_CURRENT_SOURCE_DIR}/${src} text)
    string(REPLACE "\\\\" "/" text "${text}")
    string(REGEX REPLACE "\"(logo/|settings/|bridge/|EchoXRHands\\.txt)" "\"${CMAKE_CURRENT_SOURCE_DIR}/\\1" text "${text}")
    file(WRITE ${CMAKE_BINARY_DIR}/${name} "${text}")
endfunction()
rc_copy(bridge.rc bridge/bridge.rc)
rc_copy(settings.rc settings/settings.rc)

include(FetchContent)
FetchContent_Declare(detours
    URL https://github.com/microsoft/Detours/archive/refs/tags/v4.0.1.tar.gz
    URL_HASH SHA256=75df7f1f084acaf83c3b96a90328e93823c2506a97363d50556f1ee700c81f68
    DOWNLOAD_EXTRACT_TIMESTAMP TRUE
    SOURCE_SUBDIR no-cmake-project
)
FetchContent_MakeAvailable(detours)
set(D ${detours_SOURCE_DIR}/src)
add_library(detours STATIC
    ${D}/detours.cpp ${D}/modules.cpp ${D}/disasm.cpp ${D}/image.cpp ${D}/creatwth.cpp
    ${D}/disolx86.cpp ${D}/disolx64.cpp ${D}/disolia64.cpp ${D}/disolarm.cpp
    ${D}/disolarm64.cpp)
target_include_directories(detours PUBLIC ${D})
target_compile_definitions(detours PRIVATE WIN32_LEAN_AND_MEAN _WIN32_WINNT=0x0601)
target_compile_options(detours PRIVATE /W0)
set_target_properties(detours PROPERTIES MSVC_RUNTIME_LIBRARY MultiThreadedDLL)

# The plugin: /MD /EHa, as build.bat.
add_library(EchoXRHands SHARED plugin/handtracking.cpp plugin/htv_net.cpp)
target_include_directories(EchoXRHands PRIVATE third_party plugin)
target_link_libraries(EchoXRHands PRIVATE detours ws2_32 winhttp user32)
target_compile_options(EchoXRHands PRIVATE /EHa /W3)
set_target_properties(EchoXRHands PROPERTIES
    MSVC_RUNTIME_LIBRARY MultiThreadedDLL
    RUNTIME_OUTPUT_DIRECTORY ${OUT} LIBRARY_OUTPUT_DIRECTORY ${OUT} ARCHIVE_OUTPUT_DIRECTORY ${CMAKE_BINARY_DIR})

# The finger bridge.
add_executable(EchoXRHandsBridge bridge/bridge.cpp ${CMAKE_BINARY_DIR}/bridge.rc)
target_include_directories(EchoXRHandsBridge PRIVATE third_party common)
target_link_libraries(EchoXRHandsBridge PRIVATE ws2_32)
target_compile_options(EchoXRHandsBridge PRIVATE /EHsc /W3)
set_target_properties(EchoXRHandsBridge PROPERTIES OUTPUT_NAME EchoXRHands
    MSVC_RUNTIME_LIBRARY MultiThreadedDLL RUNTIME_OUTPUT_DIRECTORY ${OUT})

# The settings window: static CRT, Unicode, GUI.
add_executable(EchoXRSettings WIN32 settings/settings.cpp ${CMAKE_BINARY_DIR}/settings.rc)
set_property(SOURCE ${CMAKE_BINARY_DIR}/settings.rc APPEND PROPERTY INCLUDE_DIRECTORIES ${CMAKE_CURRENT_SOURCE_DIR}/settings)
target_include_directories(EchoXRSettings PRIVATE common)
target_compile_definitions(EchoXRSettings PRIVATE UNICODE _UNICODE)
target_compile_options(EchoXRSettings PRIVATE /EHsc /W3 /utf-8)
target_link_libraries(EchoXRSettings PRIVATE user32 gdi32 gdiplus dwmapi shell32 ole32 ws2_32)
set_target_properties(EchoXRSettings PROPERTIES
    MSVC_RUNTIME_LIBRARY MultiThreaded RUNTIME_OUTPUT_DIRECTORY ${OUT})
# Its manifest is in settings.rc already.
target_link_options(EchoXRSettings PRIVATE /MANIFEST:NO)

foreach(f EchoXRHands.txt bridge/htv_actions.json bridge/htv_bindings_knuckles.json)
    configure_file(${f} ${OUT}/ COPYONLY)
endforeach()
