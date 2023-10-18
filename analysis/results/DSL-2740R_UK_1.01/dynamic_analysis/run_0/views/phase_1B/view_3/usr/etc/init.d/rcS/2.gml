graph [
  directed 1
  node [
    id 0
    label "pipe_50_4_5"
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
    label "/usr/etc/init.d/rcS"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/bin/sed"
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
    source 1
    target 0
  ]
]
