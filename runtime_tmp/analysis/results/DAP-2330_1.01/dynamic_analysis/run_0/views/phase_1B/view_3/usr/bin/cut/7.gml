graph [
  directed 1
  node [
    id 0
    label "pipe_2368_4_5"
    kind "channel"
  ]
  node [
    id 1
    label "/bin/date"
    kind "executable"
    listening 0
  ]
  node [
    id 2
    label "/usr/sbin/time"
    kind "executable"
    listening 0
  ]
  node [
    id 3
    label "/usr/bin/cut"
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
]
