graph [
  directed 1
  node [
    id 0
    label "pipe_52_3_4"
    kind "channel"
  ]
  node [
    id 1
    label "/bin/cat"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/etc/init.d/S03config.sh"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/bin/sed"
    kind "executable"
    listening 0
  ]
  node [
    id 4
    label "/usr/sbin/devdata"
    kind "executable"
    listening 0
  ]
  node [
    id 5
    label "/usr/bin/expr"
    kind "executable"
    listening 0
  ]
  node [
    id 6
    label "/usr/bin/printf"
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
  edge [
    source 3
    target 0
  ]
  edge [
    source 4
    target 0
  ]
  edge [
    source 5
    target 0
  ]
  edge [
    source 6
    target 0
  ]
]
