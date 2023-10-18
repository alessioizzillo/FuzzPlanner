graph [
  directed 1
  node [
    id 0
    label "socket(domain:1, type:2, protocol:0){path:/var/run/servd_ctrl_usock}"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/service"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/sbin/servd"
    kind "executable"
    listening 0
  ]
  edge [
    source 0
    target 2
  ]
  edge [
    source 0
    target 1
  ]
  edge [
    source 1
    target 0
  ]
  edge [
    source 2
    target 0
  ]
]
