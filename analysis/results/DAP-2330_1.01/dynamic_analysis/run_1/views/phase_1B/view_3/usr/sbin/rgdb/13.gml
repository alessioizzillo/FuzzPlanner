graph [
  directed 1
  node [
    id 0
    label "pipe_1443_3_4"
    kind "channel"
  ]
  node [
    id 1
    label "/usr/sbin/rgdb"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/etc/templates/dhcpd.sh"
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
