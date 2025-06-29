graph [
  directed 1
  node [
    id 0
    label "pipe_1042_9_10"
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
    label "/usr/sbin/scut"
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
