
set(UNIFDEF_EXECUTABLE ${CMAKE_BINARY_DIR}/bin/unifdef CACHE FILEPATH "Path to unifdef executable")

add_executable(unifdef EXCLUDE_FROM_ALL unifdef.c)
