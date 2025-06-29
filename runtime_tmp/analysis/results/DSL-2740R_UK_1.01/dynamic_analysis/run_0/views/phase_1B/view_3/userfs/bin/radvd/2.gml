graph [
  directed 1
  node [
    id 0
    label "virtual_file{path:/proc/sys/net/ipv6/conf/all/forwarding}"
    kind "channel"
  ]
  node [
    id 1
    label "/bin/echo"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/userfs/bin/radvd"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 1
    target 0
  ]
]
