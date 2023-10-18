graph [
  directed 1
  node [
    id 0
    label "file{path:/etc/mac.conf}"
    kind "channel"
  ]
  node [
    id 1
    label "/sbin/ifconfig"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/script/wan_start.sh"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/bin/sh"
    kind "executable"
    listening 0
  ]
  node [
    id 4
    label "/usr/script/ether_mac.sh"
    kind "executable"
    listening 0
  ]
  node [
    id 5
    label "/usr/script/wan_stop.sh"
    kind "executable"
    listening 0
  ]
  node [
    id 6
    label "/usr/etc/init.d/rcS"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 0
    target 3
  ]
  edge [
    source 0
    target 4
  ]
  edge [
    source 0
    target 5
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 6
    target 0
  ]
]
