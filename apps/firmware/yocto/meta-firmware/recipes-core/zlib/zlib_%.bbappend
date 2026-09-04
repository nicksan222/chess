# Fetch Yocto's checksum-verified mirror instead of zlib's mutable current-release URL.
SRC_URI:remove = "https://zlib.net/${BP}.tar.gz"
SRC_URI:prepend = "https://downloads.yoctoproject.org/mirror/sources/${BP}.tar.gz "
